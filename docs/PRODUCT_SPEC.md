# Comotion Web App — Product Specification v1.0

**Document Version:** 1.0  
**Date:** 2026-03-08  
**Status:** Draft  
**Author:** MaxZA / Comotion Team

---

## Table of Contents

1. [Overview](#1-overview)
2. [Product Shape](#2-product-shape)
3. [Tech Stack](#3-tech-stack)
4. [Coach Workflow](#4-coach-workflow)
5. [Screens](#5-screens)
6. [Metrics](#6-metrics)
7. [CSV Field Mapping](#7-csv-field-mapping)
8. [Data Model](#8-data-model)
9. [Processing Pipeline](#9-processing-pipeline)
10. [Reports](#10-reports)
11. [Metric Definitions](#11-metric-definitions)
12. [Build Order](#12-build-order)
13. [Out of Scope (v1)](#13-out-of-scope-v1)

---

## 1. Overview

Comotion Web is a **coach-facing analytics web app** for processing and visualising data from Comotion wearable trackers worn during field hockey matches. It is not a generic BI tool — it is purpose-built for the coach workflow: upload data, review match reports, track player development over a season.

**Target users:** Coaches, team managers, and administrators at school, club, and elite level.

**Key principle:** Dead simple for coaches. Complexity lives in the processing pipeline, not the UI.

---

## 2. Product Shape

For v1, this is a **custom web app for coaches and admins** — not a generic dashboard tool.

**Architecture in one line:**  
Custom web app + Python analytics + Postgres + object storage + embedded Superset dashboards.

**Scale-up path:** Add ClickHouse once raw sensor/time-series volume gets large.

---

## 3. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React / Next.js | SSR, fast iteration, large ecosystem |
| **Backend API** | Python / FastAPI | Native file upload + background tasks; fits upload/process/report flow |
| **Metadata DB** | PostgreSQL | Reliable, supports complex queries, row-level security |
| **Raw file storage** | S3-compatible object store | Cheap bulk storage for CSVs and raw sensor data |
| **Analytics UI** | Embedded Superset | Official embedding support, guest tokens, row-level security — fits multi-tenant safely |
| **Async processing** | Worker queue (Celery / ARQ) | CSV processing, metric computation, PDF generation |
| **Future scale** | ClickHouse | Time-series analytics for large-volume telemetry history |

**Why Superset over Metabase:** Superset's row-level security is open-source. Metabase's equivalent is Pro/Enterprise only — problematic for multi-tenant (many clubs/teams/countries).

---

## 4. Coach Workflow

The experience should be:

```
Create Match → Upload CSV(s) → System validates & processes → Coach opens match report
     → Coach drills into player / quarter / heatmap / season trends → Coach exports PDF/link
```

**Not:** "Open BI tool, choose file, build charts."

---

## 5. Screens

### 5A. Match Setup / Upload

**Purpose:** Get raw data into the system cleanly.

**Fields:**
- Match date
- Opponent
- Age group
- Competition
- Venue
- Squad list
- Player ↔ device assignment
- *(Optional)* Roster positions
- *(Optional)* Quarter start/end confirmation

**Post-upload quality flags:**
- Missing rows
- GPS weak
- Too few satellites
- Impossible jumps
- No event markers
- Audio unusable

---

### 5B. Match Overview

**First screen a coach sees after upload.**

| Section | Content |
|---------|---------|
| **KPI cards** | Team total distance, avg distance/min, top speed leaders, high-speed distance leaders, acceleration/deceleration leaders, "load" leaders |
| **Team trend** | Quarter-by-quarter trend line |
| **Player ranking** | Sortable table underneath |
| **Quick flags** | Overloaded, underloaded, unusually low playing time, poor data quality |

---

### 5C. Player Card

**The most valuable single screen for coaches.**

For one player, show:
- Minutes played
- Total distance
- Distance/min
- Top speed
- High-speed distance
- Sprint count
- Acceleration count
- Deceleration count
- Load score
- Quarter splits
- Rolling 1-min / 3-min / 5-min peak intensity
- Heatmap
- Timeline with event markers

---

### 5D. Spatial / Pitch Map

**Where the product feels "sports-specific."**

- Heatmap
- Average position
- Movement trail
- Zone occupancy (attacking / middle / defensive third)
- Left / center / right lane occupancy
- Intensity heatmap

---

### 5E. Timeline

**How the match evolved.**

- Speed over time
- Load over time
- Acceleration bursts
- Event markers
- Quarter boundaries
- Compare 2 players on same chart

---

### 5F. Season Workload

**Critical once teams use the product weekly.**

- Last 5 matches
- Last 28 days
- Acute vs rolling baseline
- Player vs own baseline
- Player vs positional baseline
- Workload trend
- Return-to-play progression view

---

### 5G. Admin / Organization

**Needed for scale across countries and clubs.**

- Organizations
- Teams
- Users & roles
- Players
- Devices
- Competitions
- Data retention settings

---

## 6. Metrics

### 6A. Exposure / Playing Time

| Metric | Description |
|--------|-------------|
| Minutes played | Total match time |
| Active time | Time with movement above threshold |
| Time on pitch | Clock time between first and last data |
| Time per quarter | Split by Q1–Q4 |

### 6B. Running / Movement

| Metric | Description |
|--------|-------------|
| Total distance | Sum of filtered GPS point-to-point distances |
| Distance per minute | Total distance ÷ minutes played |
| Average speed | Mean speed during active periods |
| Top speed | Highest accepted speed after quality filtering |
| Speed zone time | Time in each speed zone |
| Speed zone distance | Distance in each speed zone |
| High-speed distance | Distance above configurable HSR threshold |
| Sprint count | Events above sprint threshold with minimum duration |

### 6C. Explosive Actions

| Metric | Description |
|--------|-------------|
| Acceleration count | Events above acceleration threshold + min duration |
| Deceleration count | Events above deceleration threshold + min duration |
| High-intensity accel/decel count | Higher threshold variant |
| Repeated effort bouts | Clusters of explosive actions |
| Max acceleration | Peak acceleration value |
| Max deceleration | Peak deceleration value |

### 6D. Load / Fatigue Pattern

| Metric | Description |
|--------|-------------|
| Total load score | Comotion Load (proprietary combined IMU index) |
| Load per minute | Load ÷ minutes played |
| Quarter load | Load split by Q1–Q4 |
| Rolling peak 1/3/5 min | Highest intensity window at each duration |
| Q1 vs Q4 drop-off | Fatigue indicator |
| Second-half vs first-half ratio | Endurance indicator |

### 6E. Spatial / Tactical

| Metric | Description |
|--------|-------------|
| Heatmap | Position density on pitch |
| Average position | Mean lat/lng during play |
| Zone occupancy | % time in attack/mid/defense thirds |
| Lane occupancy | % time in left/center/right lanes |
| Width and depth tendency | Spread of movement |
| Work rate by zone | Distance/min in each zone |

### Why These Metrics Matter

Field hockey demands vary by position and quarter. The product should **always compare players against their role** and show **quarter splits**, not just full-match averages. Research supports using moving windows (1–10 min peaks) rather than only full-match averages. Acceleration/deceleration metrics are sensitive to sampling, thresholds, filtering, and signal quality — Comotion should define **consistent metric rules** and stick to them.

FIH rules: four 15-minute quarters with breaks. The app must be **quarter-aware by design**.

---

## 7. CSV Field Mapping

### timestamp
- **Use for:** elapsed time, sample interval, quarter segmentation, rolling windows, event alignment, time on pitch, burst detection
- **Derived:** `elapsed_s`, `quarter`, `window_1m/3m/5m`, `is_gap`, `segment_id`

### ax, ay, az (accelerometer)
- **Use for:** resultant acceleration, movement load, impact spikes, burst detection
- **Derived:** `accel_mag = sqrt(ax² + ay² + az²)`, filtered dynamic acceleration, jerk, IMU load contribution
- **⚠️ Do not expose raw axes to coaches.** Use them underneath a simple metric like Comotion Load.

### gx, gy, gz (gyroscope)
- **Use for:** rotational intensity, turning load, rapid body rotation events
- **Derived:** `gyro_mag = sqrt(gx² + gy² + gz²)`, turn intensity index, rotational load contribution
- Especially useful when GPS path alone misses sharp body actions.

### lat, lng (raw GPS)
- **Use for:** fallback GPS path, raw-vs-filtered validation, anomaly detection

### lat_filt, lng_filt (filtered GPS)
- **Drive almost all spatial and movement metrics.**
- **Derived:** point-to-point distance, smoothed path, speed cross-check, heatmap cells, zone occupancy, average position, direction of travel

### speed
- **Use for:** speed zones, top speed, HSR distance, sprint count, speed-over-time charts
- **Derived:** `speed_zone`, `hsr_distance`, `sprint_events`, `peak_speed`

### course
- **Use for:** direction change rate, turn detection, route smoothing, attack direction normalization
- **Derived:** `bearing_change`, `turn_event`, `change_of_direction_index`

### sats (satellite count)
- **Use for:** GPS quality score, confidence flags, exclusion logic
- **Derived:** `gps_quality`, `is_low_quality`, `confidence_weight`
- **⚠️ Very important.** If satellites are poor, the app should **visibly reduce confidence** in distance/speed outputs.

### audio_rms, audio_peak, audio_zcr
- **v1:** Store but keep coach-facing features to v2.
- **Possible uses:** whistle event candidate, stick-hit/crowd spike, sync anchor for external video, ambient noise quality indicator.

### event
- **Use heavily.** This is gold if reliable.
- **Use for:** quarter starts/ends, substitutions, goals, penalty corners, cards, coach annotations, sync anchors
- **Derived:** `event_type`, `phase_of_play`, `segment_label`

---

## 8. Data Model

### Core Metadata Tables

```
organizations
users
teams
players
devices
seasons
competitions
matches
team_matches
player_match_assignments
```

### Raw Ingest Tables

```
uploads
upload_files
processing_jobs
processing_errors
```

### Sensor / Session Tables

```
player_match_sessions
raw_file_manifest
sample_quality_summary
```

### Analytics Tables

**Do not make coaches query raw CSV rows directly.** Store raw files in object storage and write derived tables:

```
player_match_summary
player_match_quarter_summary
player_match_window_summary       (rolling peaks)
player_match_zone_summary         (spatial)
player_match_event_summary
player_match_peaks                (1/3/5 min peaks)
team_match_summary
```

**Scale-up path:**
- Raw / dense time-series → ClickHouse or Parquet
- App metadata + summary tables → Postgres

---

## 9. Processing Pipeline

### Stage 1: Ingest
- Upload CSV
- Validate schema/header
- Validate row count
- Validate timestamp ordering
- Validate player/device/match linkage

### Stage 2: Clean
- Remove duplicates
- Flag missing timestamps
- Flag impossible coordinates
- Flag speed spikes
- Flag low-satellite periods

### Stage 3: Enrich
- Compute elapsed time
- Identify gaps
- Infer or apply quarter boundaries
- Normalize pitch orientation
- Map coordinates to pitch zones

### Stage 4: Derive Metrics
- Running metrics
- Acceleration/deceleration events
- Load metrics
- Rolling peaks
- Spatial summaries
- Event-aligned segments

### Stage 5: Publish
- Update match overview
- Update player cards
- Update season workload
- Generate report PDF

---

## 10. Reports

### Match Report PDF

One-page summary for quick sharing:
- Top 5 KPIs
- Player ranking table
- Quarter trend
- One heatmap
- "Coach notes" section

### Interactive Match Dashboard

For in-depth analysis:
- Filter by player / quarter / position
- Compare players
- Hover on timeline
- Click heatmap
- Export tables

### Player Trend Report

For player development:
- Recent matches
- Peak speed trend
- Load trend
- Workload consistency
- Best match / worst match markers

---

## 11. Metric Definitions (v1 Dictionary)

To avoid confusion, define a small dictionary and freeze it:

| Metric | Definition |
|--------|-----------|
| **Distance** | From filtered GPS positions only |
| **Top speed** | Highest accepted speed after quality filtering |
| **High-speed running** | Configurable threshold by age/sex/level |
| **Sprint** | Configurable higher threshold + minimum duration |
| **Acceleration event** | Threshold + minimum duration |
| **Comotion Load** | Proprietary combined IMU load index, consistent within product |
| **Quarter intensity** | distance/min + high-speed distance/min + accel count (normalized) |

**Every threshold must be configurable at:**
- Organization level
- Age-group level
- Sex
- Competition level

This matters because schoolboy, club, and elite women's/men's hockey should **not** all use one rigid setting.

---

## 12. Build Order

### Phase 1 — Core (MVP)
- Upload flow
- Match overview
- Player card
- Basic heatmap
- PDF export

### Phase 2 — Depth
- Quarter comparison
- Rolling peaks
- Team comparison
- Season workload trends

### Phase 3 — Intelligence
- Event segmentation
- Audio-assisted event detection
- Video sync
- Benchmarking by position and competition

---

## 13. Out of Scope (v1)

Do **not** attempt in v1:
- Automatic tactical classification
- AI-generated coaching advice
- Injury prediction
- Automatic substitution recommendations
- Automatic video breakdown
- Cross-team benchmarking across the world
- Raw gyroscope/accelerometer plots for coaches
- Audio charts for coaches
- Black-box injury risk score

Instead, **nail:**
- ✅ Reliable uploads
- ✅ Clear player cards
- ✅ Quarter analysis
- ✅ Heatmaps
- ✅ Trend views
- ✅ Trustworthy metric definitions

**That is what gets adoption.**

---

## Appendix: Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Coach       │────▶│  Next.js     │────▶│  FastAPI      │
│  Browser     │◀────│  Frontend    │◀────│  Backend      │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                    ┌───────────────┬────────────┼────────────┐
                    │               │            │            │
               ┌────▼─────┐  ┌─────▼────┐  ┌───▼────┐  ┌───▼────────┐
               │ Postgres  │  │ S3/Minio  │  │ Worker │  │ Superset   │
               │ (metadata │  │ (raw CSV  │  │ Queue  │  │ (embedded  │
               │  + summary│  │  storage) │  │ (async │  │  analytics)│
               │  tables)  │  │           │  │  proc) │  │            │
               └──────────┘  └──────────┘  └────────┘  └────────────┘
                                                │
                                        ┌───────▼───────┐
                                        │  ClickHouse   │
                                        │  (future:     │
                                        │   time-series)│
                                        └───────────────┘
```
