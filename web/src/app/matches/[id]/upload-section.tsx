"use client";

import { useState, useRef } from "react";
import type { Upload } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UploadSection({ matchId, initialUploads }: { matchId: string; initialUploads: Upload[] }) {
  const [uploads, setUploads] = useState<Upload[]>(initialUploads);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);

    for (const file of Array.from(files)) {
      if (!file.name.toLowerCase().endsWith(".csv")) continue;
      const form = new FormData();
      form.append("file", file);

      try {
        const res = await fetch(`${API}/api/v1/matches/${matchId}/upload`, {
          method: "POST",
          body: form,
        });
        if (res.ok) {
          const upload = await res.json();
          setUploads((prev) => [upload, ...prev]);
        }
      } catch {}
    }

    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800">
      <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Uploads</h2>
        <span className="text-xs text-gray-500">{uploads.length} file(s)</span>
      </div>

      {/* Drop zone */}
      <div
        className={`mx-6 mt-4 mb-2 border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
          ${dragOver ? "border-emerald-500 bg-emerald-900/10" : "border-gray-700 hover:border-gray-600"}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" accept=".csv" multiple hidden onChange={(e) => handleFiles(e.target.files)} />
        {uploading ? (
          <p className="text-yellow-400 text-sm">Uploading...</p>
        ) : (
          <>
            <p className="text-gray-400">Drop CSV files here or click to browse</p>
            <p className="text-gray-600 text-xs mt-1">One CSV per player/device</p>
          </>
        )}
      </div>

      {/* Upload list */}
      {uploads.length > 0 && (
        <div className="px-6 pb-4 mt-2">
          <div className="space-y-2">
            {uploads.map((u) => (
              <div key={u.id} className="flex items-center justify-between bg-gray-800/50 rounded px-3 py-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">📄</span>
                  <span className="text-white">{u.filename}</span>
                  {u.row_count && <span className="text-gray-500 text-xs">({u.row_count} rows)</span>}
                </div>
                <div className="flex items-center gap-2">
                  {u.quality_flags?.gps_quality_pct !== undefined && (
                    <span className={`text-xs ${u.quality_flags.gps_quality_pct > 80 ? "text-emerald-400" : u.quality_flags.gps_quality_pct > 50 ? "text-yellow-400" : "text-red-400"}`}>
                      GPS {u.quality_flags.gps_quality_pct}%
                    </span>
                  )}
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    u.status === "done" ? "bg-emerald-900/50 text-emerald-300" :
                    u.status === "processing" ? "bg-yellow-900/50 text-yellow-300" :
                    u.status === "error" ? "bg-red-900/50 text-red-300" :
                    "bg-gray-700 text-gray-400"
                  }`}>{u.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
