# BLE Log Transfer Spec — Tracker → Phone → Cloud

**Version:** 1.0  
**Date:** 2026-03-08  
**Status:** Draft  

## Overview

Transfer SD card logs from tracker to web dashboard via the phone app as relay.

```
Tracker (SD card) --BLE NUS--> Phone App --HTTPS--> Web API --Processing--> Dashboard
```

---

## 1. Firmware NUS Protocol

All commands and responses go over Nordic UART Service (NUS).  
- **NUS TX** (tracker → phone): `6e400003-b5a3-f393-e0a9-e50e24dcca9e`  
- **NUS RX** (phone → tracker): `6e400002-b5a3-f393-e0a9-e50e24dcca9e`

### 1.1 Command Format

Commands are UTF-8 strings terminated by `\n`. Responses are binary or UTF-8 depending on command.

| Command | Description | Response |
|---------|-------------|----------|
| `LIST\n` | List log files on SD card | `FILE:<filename>,<bytes>,<timestamp>\n` per file, then `END_LIST\n` |
| `DUMP:<filename>\n` | Start streaming a file | Binary chunks, then `END_DUMP\n` |
| `DUMP_LATEST\n` | Stream the most recent log file | Same as DUMP |
| `DELETE:<filename>\n` | Delete a file after successful upload | `OK\n` or `ERR:<reason>\n` |
| `STATUS\n` | SD card status | `SD:<free_kb>,<total_kb>,<file_count>\n` |
| `ABORT\n` | Cancel in-progress transfer | `OK\n` |

### 1.2 DUMP Protocol (binary transfer)

After receiving `DUMP:<filename>\n`, tracker sends:

```
HEADER:  "XFER:<filename>,<total_bytes>,<crc32>\n"    (UTF-8)
CHUNKS:  [seq_u16_le][payload_bytes]                    (binary, up to 240 bytes each)
FOOTER:  "END_DUMP:<actual_bytes>,<actual_crc32>\n"    (UTF-8)
```

**Chunk format (242 bytes max):**
```
Byte 0-1:  Sequence number (uint16 LE, starting at 0)
Byte 2-N:  Payload (up to 240 bytes)
```

**Flow control:**
- Tracker sends chunks continuously (no ACK per chunk — BLE stack handles flow control)
- Phone can send `PAUSE\n` / `RESUME\n` if buffer is full
- Phone sends `ACK:<last_seq>\n` every 50 chunks (tracker resends from last ACK on timeout)

**Transfer speed estimate:**
- BLE 5.0 with DLE (251 byte MTU): ~240 bytes/chunk × 20 chunks/sec = **4.8 KB/s**
- With Coded PHY connection (not adv): similar throughput but longer range
- 2MB CSV file: **~7 minutes**
- 2MB gzipped (~300KB): **~1 minute** ← recommended

### 1.3 Compression

Tracker should gzip the file before sending if possible.

**Zephyr approach:**
- `CONFIG_MINIZ=y` gives lightweight zlib
- Compress in 4KB chunks, stream compressed chunks over NUS
- Header becomes: `XFER:<filename>.gz,<compressed_bytes>,<crc32>\n`
- Phone detects `.gz` suffix and decompresses before upload

**If compression is too heavy for nRF52840 RAM:**
- Send raw CSV — phone app handles it fine, just slower
- Consider binary log format on SD card instead (half the size of CSV)

### 1.4 Firmware Implementation (Zephyr)

```c
// In nus_command_handler():
if (strncmp(buf, "LIST", 4) == 0) {
    sd_list_files();  // sends FILE: lines over NUS TX
} else if (strncmp(buf, "DUMP:", 5) == 0) {
    char *filename = buf + 5;
    sd_start_transfer(filename);  // spawns transfer thread
} else if (strncmp(buf, "DUMP_LATEST", 11) == 0) {
    sd_start_transfer(NULL);  // NULL = most recent file
} else if (strncmp(buf, "DELETE:", 7) == 0) {
    sd_delete_file(buf + 7);
} else if (strncmp(buf, "ABORT", 5) == 0) {
    sd_abort_transfer();
} else if (strncmp(buf, "ACK:", 4) == 0) {
    uint16_t seq = atoi(buf + 4);
    sd_ack_received(seq);
}

// Transfer thread (runs in background, doesn't block sensor sampling)
void sd_transfer_thread(void *filename) {
    FIL file;
    f_open(&file, filename, FA_READ);
    uint32_t total = f_size(&file);
    uint32_t crc = 0;
    
    // Send header
    char header[128];
    snprintf(header, sizeof(header), "XFER:%s,%u,%08X\n", filename, total, 0);
    nus_send(header, strlen(header));
    
    // Send chunks
    uint16_t seq = 0;
    uint8_t chunk[242];
    UINT bytes_read;
    while (f_read(&file, chunk + 2, 240, &bytes_read) == FR_OK && bytes_read > 0) {
        if (transfer_aborted) break;
        chunk[0] = seq & 0xFF;
        chunk[1] = (seq >> 1) & 0xFF;
        nus_send(chunk, bytes_read + 2);
        crc = crc32(crc, chunk + 2, bytes_read);
        seq++;
        
        // Yield to let BLE stack flush
        k_sleep(K_MSEC(5));
    }
    
    // Send footer
    char footer[128];
    snprintf(footer, sizeof(footer), "END_DUMP:%u,%08X\n", total, crc);
    nus_send(footer, strlen(footer));
    
    f_close(&file);
}
```

### 1.5 SD Card File Naming & Timestamps

```
/logs/
  log_0001.csv            ← sequential log files
  log_0002.csv
  counter.txt             ← single number: next file index (persists across reboots)
```

**Sequential naming with crash safety:**
- On boot: read `counter.txt` → next file = `log_NNNN.csv`
- If `counter.txt` missing: scan `/logs/` for highest existing number + 1
- On session start: increment counter, write to `counter.txt`, create new file
- This avoids filename collisions even after unexpected power loss

**Timestamps come from the CSV data itself (no index file):**

When firmware receives `LIST\n`, it scans each `.csv` file:
1. Open file, read **first 512 bytes** → find first row with a valid GPS datetime
2. Seek to **last 1024 bytes** → find last row with a valid GPS datetime
3. Send `FILE:<name>,<bytes>,<start_epoch>,<end_epoch>\n`

If no valid GPS datetime found in a file, send `0` for that epoch.

This is crash-proof — no separate index to maintain. The data is always
in the CSV. Even if the device dies mid-session, the timestamps are
whatever GPS data was already written.

**CSV row timestamp format:**
Each CSV row should have a `timestamp` column (Unix epoch seconds from GPS UTC).
Firmware scans for the first/last numeric value in that column position.

**Example LIST response:**
```
FILE:log_0001.csv,245760,1709913600,1709917200\n
FILE:log_0002.csv,189440,1709920800,1709924400\n
FILE:log_0003.csv,51200,0,0\n
END_LIST\n
```

Note: `log_0003.csv` has `0,0` — no GPS fix during that session.
App shows filename instead of date/time for those files.

**Performance:** Reading first 512 + last 1024 bytes per file is fast —
~20 files takes 1-2 seconds. App shows "Listing files..." spinner during this.

**App displays files grouped by date (newest first):**
```
┌─────────────────────────────────────────────┐
│  8 Mar 2026                                 │
│  ┌──────────────────────────────────────┐   │
│  │ ⏱  14:30 – 15:45                    ☁  │
│  │    1h 15m · 2.1 MB · ~7 min         │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │ ⏱  16:00 – 16:45                    ☁  │
│  │    45 min · 1.4 MB · ~5 min         │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  7 Mar 2026                                 │
│  ┌──────────────────────────────────────┐   │
│  │ ⏱  09:15 – 10:30                    ☁  │
│  │    1h 15m · 2.0 MB · ~7 min         │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Unknown date                               │
│  ┌──────────────────────────────────────┐   │
│  │ 📄 log_0003.csv                     ☁  │
│  │    50 KB · ~10s                      │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

Coach sees date, time range, and duration — picks the right match instantly.
Files without GPS timestamps fall to the bottom with just the filename.

---

## 2. App — BLE Download Flow

### 2.1 UI Flow

```
Player List Screen
  └── Tap player → Player Card
       └── "Download Logs" button (only visible when BLE connected)
            └── Log Transfer Sheet
                 ├── Shows available files (from LIST command)
                 ├── Tap file → download progress bar
                 ├── "Download Latest" shortcut button
                 └── After download: "Upload to Cloud" button
```

### 2.2 Transfer Service (`lib/data/services/log_transfer_service.dart`)

```dart
enum TransferState { idle, listing, downloading, uploading, done, error }

class LogTransferService extends ChangeNotifier {
  TransferState state = TransferState.idle;
  double progress = 0.0;  // 0.0 - 1.0
  String? currentFile;
  String? errorMessage;
  List<LogFileInfo> availableFiles = [];
  
  // BLE connection (reuse existing NUS connection)
  final BluetoothCharacteristic _nusTx;
  final BluetoothCharacteristic _nusRx;
  
  // Download buffer
  final List<int> _downloadBuffer = [];
  int _expectedBytes = 0;
  int _expectedCrc = 0;
  int _lastAckSeq = 0;
  
  /// List files on tracker SD card
  Future<void> listFiles() async {
    state = TransferState.listing;
    notifyListeners();
    
    availableFiles.clear();
    await _sendCommand('LIST\n');
    // Parse FILE: responses in NUS notification handler
  }
  
  /// Download a specific file
  Future<List<int>> downloadFile(String filename) async {
    state = TransferState.downloading;
    progress = 0.0;
    currentFile = filename;
    _downloadBuffer.clear();
    notifyListeners();
    
    await _sendCommand('DUMP:$filename\n');
    
    // Wait for transfer to complete (NUS notifications fill buffer)
    // Returns raw bytes
    return _downloadBuffer;
  }
  
  /// Download latest and upload to cloud in one tap
  Future<void> downloadAndUpload(String matchId, String? playerId) async {
    // 1. Download
    final bytes = await downloadFile('latest');
    
    // 2. Decompress if gzipped
    List<int> csvBytes;
    if (_isGzipped(bytes)) {
      csvBytes = gzip.decode(bytes);
    } else {
      csvBytes = bytes;
    }
    
    // 3. Upload to web API
    state = TransferState.uploading;
    notifyListeners();
    
    await _uploadToCloud(matchId, playerId, csvBytes);
    
    state = TransferState.done;
    notifyListeners();
  }
  
  /// Upload CSV bytes to web API
  Future<void> _uploadToCloud(String matchId, String? playerId, List<int> csvBytes) async {
    final uri = Uri.parse('$apiBaseUrl/api/v1/matches/$matchId/upload');
    final request = http.MultipartRequest('POST', uri)
      ..files.add(http.MultipartFile.fromBytes(
        'file',
        csvBytes,
        filename: currentFile ?? 'tracker_log.csv',
      ));
    
    if (playerId != null) {
      request.fields['player_id'] = playerId;
    }
    
    // Add auth token
    final token = await AuthService.instance.getToken();
    if (token != null) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    
    final response = await request.send();
    if (response.statusCode != 200) {
      throw Exception('Upload failed: ${response.statusCode}');
    }
  }
  
  /// Handle incoming NUS notifications (called from BLE layer)
  void onNusData(List<int> data) {
    final str = utf8.decode(data, allowMalformed: true);
    
    if (str.startsWith('FILE:')) {
      // Parse file listing
      final parts = str.substring(5).trim().split(',');
      availableFiles.add(LogFileInfo(
        filename: parts[0],
        bytes: int.parse(parts[1]),
        timestamp: parts.length > 2 ? parts[2] : null,
      ));
      notifyListeners();
    } else if (str.startsWith('END_LIST')) {
      state = TransferState.idle;
      notifyListeners();
    } else if (str.startsWith('XFER:')) {
      // Parse transfer header
      final parts = str.substring(5).trim().split(',');
      _expectedBytes = int.parse(parts[1]);
      _expectedCrc = int.parse(parts[2], radix: 16);
    } else if (str.startsWith('END_DUMP:')) {
      // Verify CRC
      final parts = str.substring(9).trim().split(',');
      final actualBytes = int.parse(parts[0]);
      final actualCrc = int.parse(parts[1], radix: 16);
      // TODO: verify CRC32 match
      state = TransferState.idle;
      notifyListeners();
    } else if (state == TransferState.downloading) {
      // Binary chunk: first 2 bytes = seq, rest = payload
      if (data.length >= 3) {
        final seq = data[0] | (data[1] << 8);
        _downloadBuffer.addAll(data.sublist(2));
        progress = _downloadBuffer.length / _expectedBytes.clamp(1, double.infinity);
        
        // ACK every 50 chunks
        if (seq - _lastAckSeq >= 50) {
          _sendCommand('ACK:$seq\n');
          _lastAckSeq = seq;
        }
        notifyListeners();
      }
    }
  }
  
  Future<void> _sendCommand(String cmd) async {
    await _nusRx.write(utf8.encode(cmd), withoutResponse: false);
  }
}

class LogFileInfo {
  final String filename;
  final int bytes;
  final String? timestamp;
  
  LogFileInfo({required this.filename, required this.bytes, this.timestamp});
  
  String get sizeFormatted {
    if (bytes > 1024 * 1024) return '${(bytes / 1024 / 1024).toStringAsFixed(1)} MB';
    if (bytes > 1024) return '${(bytes / 1024).toStringAsFixed(0)} KB';
    return '$bytes B';
  }
}
```

### 2.3 UI — Log Transfer Sheet

```dart
class LogTransferSheet extends StatelessWidget {
  final String deviceId;
  final String matchId;
  final String? playerId;
  
  @override
  Widget build(BuildContext context) {
    return Consumer<LogTransferService>(
      builder: (context, service, _) {
        return Container(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Download Logs', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              SizedBox(height: 16),
              
              // Quick action
              ElevatedButton.icon(
                icon: Icon(Icons.cloud_upload),
                label: Text('Download Latest & Upload'),
                onPressed: service.state == TransferState.idle
                  ? () => service.downloadAndUpload(matchId, playerId)
                  : null,
              ),
              
              SizedBox(height: 16),
              
              // Progress
              if (service.state == TransferState.downloading) ...[
                Text('Downloading: ${service.currentFile}'),
                SizedBox(height: 8),
                LinearProgressIndicator(value: service.progress),
                Text('${(service.progress * 100).toStringAsFixed(0)}%'),
              ],
              
              if (service.state == TransferState.uploading)
                Text('Uploading to cloud...', style: TextStyle(color: Colors.amber)),
              
              if (service.state == TransferState.done)
                Text('✅ Upload complete!', style: TextStyle(color: Colors.green)),
              
              if (service.state == TransferState.error)
                Text('❌ ${service.errorMessage}', style: TextStyle(color: Colors.red)),
              
              // File list
              if (service.availableFiles.isNotEmpty) ...[
                SizedBox(height: 16),
                Text('Available Files:', style: TextStyle(fontWeight: FontWeight.w600)),
                ...service.availableFiles.map((f) => ListTile(
                  leading: Icon(Icons.description),
                  title: Text(f.filename),
                  subtitle: Text(f.sizeFormatted),
                  trailing: IconButton(
                    icon: Icon(Icons.download),
                    onPressed: () => service.downloadFile(f.filename),
                  ),
                )),
              ],
            ],
          ),
        );
      },
    );
  }
}
```

---

## 3. Web API — Already Done ✅

The existing upload endpoint handles everything:

```
POST /api/v1/matches/{match_id}/upload
  ?player_id=<uuid>
  &device_id=<uuid>
  Body: multipart/form-data with CSV file

→ Saves file, triggers background CSV processing
→ Computes 20+ metrics (distance, speed, HSR, sprints, load, etc.)
→ Writes PlayerMatchSummary to database
→ Dashboard updates automatically
```

---

## 4. Live Streaming (Phase 2)

For real-time dashboard during matches:

```
Tracker --BLE adv--> Phone App --WebSocket--> Web API --SSE--> Dashboard
```

**New endpoints:**
```
WS  /api/v1/matches/{match_id}/live     ← Phone connects, sends JSON packets
SSE /api/v1/matches/{match_id}/stream   ← Dashboard subscribes for live updates
```

**Phone sends (every BLE advertisement):**
```json
{
  "device_id": "AA:BB:CC:DD:EE:FF",
  "player_id": "uuid",
  "timestamp": 1709913600.123,
  "lat": -25.7479123,
  "lng": 28.2293456,
  "speed_kmh": 12.5,
  "intensity_1s": 78,
  "intensity_1min": 45,
  "heart_rate": 165,
  "battery_pct": 87
}
```

This gives the web dashboard the same real-time view the phone app currently has — but on a bigger screen with more analytics.

---

## 5. Implementation Order

| Priority | Task | Effort | Dependency |
|----------|------|--------|------------|
| **P1** | Firmware: `LIST`, `DUMP_LATEST`, `DELETE` NUS commands | 2 days | SD card logging working |
| **P1** | App: `LogTransferService` + BLE download | 1 day | Firmware NUS commands |
| **P1** | App: Upload to cloud (HTTP POST) | 0.5 day | Web API (done) |
| **P2** | App: Log Transfer Sheet UI | 0.5 day | LogTransferService |
| **P2** | Firmware: gzip compression | 1 day | Nice-to-have for speed |
| **P3** | Live WebSocket streaming | 2 days | Phase 2 feature |
| **P3** | Dashboard SSE live view | 1 day | WebSocket endpoint |

**Total for P1 (post-match upload):** ~3.5 days  
**Total for P2 (polish):** ~1.5 days  
**Total for P3 (live streaming):** ~3 days

---

## 6. Security Considerations

- Phone must authenticate with web API (JWT from Google OAuth)
- Upload endpoint validates: match exists, user has coach/admin role, file is CSV
- Device-to-phone: BLE connection is inherently short-range (~10m), low risk
- Consider adding device authentication later (shared secret in firmware)
- Delete command should only work after successful upload + CRC verification
