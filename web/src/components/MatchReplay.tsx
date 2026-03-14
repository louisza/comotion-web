"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getMatchReplay, type ReplayData, type ReplayPlayer, type ReplayPoint } from "@/lib/api";

const TILE_URL = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}";

const SPEED_OPTIONS = [1, 2, 4, 8];

const ZONE_COLORS = ["#6b7280", "#22c55e", "#eab308", "#f97316", "#ef4444"];

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** Interpolate position at time t from sorted points array */
function interpolatePosition(points: ReplayPoint[], t: number): ReplayPoint | null {
  if (points.length === 0) return null;
  if (t <= points[0].t) return points[0];
  if (t >= points[points.length - 1].t) return points[points.length - 1];

  // Binary search for bracket
  let lo = 0, hi = points.length - 1;
  while (lo < hi - 1) {
    const mid = (lo + hi) >> 1;
    if (points[mid].t <= t) lo = mid; else hi = mid;
  }

  const a = points[lo], b = points[hi];
  const frac = b.t === a.t ? 0 : (t - a.t) / (b.t - a.t);
  return {
    t,
    lat: a.lat + (b.lat - a.lat) * frac,
    lng: a.lng + (b.lng - a.lng) * frac,
    spd: a.spd + (b.spd - a.spd) * frac,
    z: frac < 0.5 ? a.z : b.z,
  };
}

/** Get trail points for last trailSec seconds */
function getTrail(points: ReplayPoint[], t: number, trailSec: number): [number, number][] {
  const trail: [number, number][] = [];
  const start = t - trailSec;
  for (const p of points) {
    if (p.t > t) break;
    if (p.t >= start) trail.push([p.lat, p.lng]);
  }
  return trail;
}

interface MatchReplayProps {
  matchId: string;
}

export default function MatchReplay({ matchId }: MatchReplayProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const trailsRef = useRef<any[]>([]);
  const LRef = useRef<any>(null);

  const [data, setData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);

  const playingRef = useRef(false);
  const speedRef = useRef(1);
  const timeRef = useRef(0);
  const rafRef = useRef<number | null>(null);
  const lastFrameRef = useRef<number>(0);

  // Fetch data
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getMatchReplay(matchId)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setError(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, [matchId]);

  // Init map
  useEffect(() => {
    if (!data || !mapRef.current || typeof window === "undefined") return;
    const init = async () => {
      const L = (await import("leaflet")).default;
      // @ts-ignore - CSS import for leaflet styles
      await import("leaflet/dist/leaflet.css");
      LRef.current = L;

      if (mapInstance.current) mapInstance.current.remove();

      // Find bounds from all player points
      let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
      let hasPoints = false;
      for (const p of data.players) {
        for (const pt of p.points) {
          hasPoints = true;
          if (pt.lat < minLat) minLat = pt.lat;
          if (pt.lat > maxLat) maxLat = pt.lat;
          if (pt.lng < minLng) minLng = pt.lng;
          if (pt.lng > maxLng) maxLng = pt.lng;
        }
      }

      const center: [number, number] = hasPoints
        ? [(minLat + maxLat) / 2, (minLng + maxLng) / 2]
        : [-25.74, 28.22];

      const map = L.map(mapRef.current!, { center, zoom: 18, maxZoom: 21, zoomControl: true });
      L.tileLayer(TILE_URL, { maxZoom: 21, maxNativeZoom: 20, attribution: "" }).addTo(map);

      if (hasPoints) {
        map.fitBounds([[minLat, minLng], [maxLat, maxLng]], { padding: [30, 30] });
      }

      mapInstance.current = map;

      // Create markers for each player
      markersRef.current = data.players.map((player) => {
        const label = player.player_name?.[0]?.toUpperCase() || "?";
        const icon = L.divIcon({
          className: "",
          html: `<div style="position:relative">
            <div id="dot-${player.player_id}" style="width:20px;height:20px;border-radius:50%;background:${player.color};border:2px solid white;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:bold;color:white;box-shadow:0 2px 6px rgba(0,0,0,0.5)">${label}</div>
            <div style="text-align:center;font-size:9px;color:white;text-shadow:0 1px 3px rgba(0,0,0,0.8);white-space:nowrap;margin-top:2px">${player.player_name}</div>
          </div>`,
          iconSize: [60, 36],
          iconAnchor: [30, 10],
        });
        const firstPt = player.points[0];
        const marker = L.marker(
          firstPt ? [firstPt.lat, firstPt.lng] : center,
          { icon, opacity: firstPt ? 1 : 0 }
        ).addTo(map);
        return marker;
      });

      // Trail polylines
      trailsRef.current = data.players.map((player) =>
        L.polyline([], { color: player.color, weight: 3, opacity: 0.5 }).addTo(map)
      );

      // Render initial frame
      updateFrame(0);
    };
    init();

    return () => {
      if (mapInstance.current) { mapInstance.current.remove(); mapInstance.current = null; }
      markersRef.current = [];
      trailsRef.current = [];
    };
  }, [data]);

  const updateFrame = useCallback((t: number) => {
    if (!data) return;
    data.players.forEach((player, i) => {
      const marker = markersRef.current[i];
      const trail = trailsRef.current[i];
      if (!marker || !trail) return;

      const pos = interpolatePosition(player.points, t);
      if (pos) {
        marker.setLatLng([pos.lat, pos.lng]);
        marker.setOpacity(1);
        // Update dot size based on speed zone
        const dotEl = document.getElementById(`dot-${player.player_id}`);
        if (dotEl) {
          const size = 18 + pos.z * 3;
          dotEl.style.width = `${size}px`;
          dotEl.style.height = `${size}px`;
          dotEl.style.borderColor = ZONE_COLORS[pos.z];
        }
      } else {
        marker.setOpacity(0);
      }

      // Trail
      const trailPts = getTrail(player.points, t, 30);
      trail.setLatLngs(trailPts);
    });
  }, [data]);

  // Animation loop
  useEffect(() => {
    playingRef.current = playing;
    speedRef.current = speed;

    if (playing) {
      lastFrameRef.current = performance.now();
      const tick = (now: number) => {
        if (!playingRef.current) return;
        const dt = (now - lastFrameRef.current) / 1000;
        lastFrameRef.current = now;
        const newTime = Math.min(timeRef.current + dt * speedRef.current, data?.duration || 0);
        timeRef.current = newTime;
        setCurrentTime(newTime);
        updateFrame(newTime);
        if (newTime >= (data?.duration || 0)) {
          setPlaying(false);
          return;
        }
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    }

    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [playing, speed, data, updateFrame]);

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!data) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const t = frac * data.duration;
    timeRef.current = t;
    setCurrentTime(t);
    updateFrame(t);
  };

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 text-center text-gray-400">
        Loading replay data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 text-center text-red-400">
        Failed to load replay: {error}
      </div>
    );
  }

  if (!data || data.players.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 text-center text-gray-500">
        No replay data available. Upload GPS data first.
      </div>
    );
  }

  const progress = data.duration > 0 ? (currentTime / data.duration) * 100 : 0;

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
      {/* Map */}
      <div ref={mapRef} style={{ height: 500 }} />

      {/* Controls */}
      <div className="px-4 py-3 border-t border-gray-800">
        {/* Scrubber */}
        <div
          className="relative h-6 bg-gray-800 rounded cursor-pointer mb-3"
          onClick={handleSeek}
        >
          {/* Quarter markers */}
          {data.quarters.map((q, i) => {
            const left = data.duration > 0 ? (q.start / data.duration) * 100 : 0;
            const width = data.duration > 0 ? ((q.end - q.start) / data.duration) * 100 : 0;
            const colors = ["#22c55e", "#3b82f6", "#eab308", "#ef4444"];
            return (
              <div
                key={i}
                className="absolute top-0 h-full rounded opacity-20"
                style={{ left: `${left}%`, width: `${width}%`, backgroundColor: colors[i % colors.length] }}
                title={`Q${i + 1}`}
              />
            );
          })}
          {/* Progress */}
          <div
            className="absolute top-0 h-full bg-emerald-500 rounded-l opacity-60"
            style={{ width: `${progress}%` }}
          />
          {/* Playhead */}
          <div
            className="absolute top-0 h-full w-1 bg-white rounded"
            style={{ left: `${progress}%` }}
          />
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setPlaying(!playing)}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium"
          >
            {playing ? "⏸ Pause" : "▶ Play"}
          </button>

          {/* Speed */}
          <div className="flex bg-gray-800 rounded-lg text-xs">
            {SPEED_OPTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-3 py-1.5 rounded-lg transition-colors ${
                  speed === s ? "bg-emerald-600 text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Time */}
          <span className="text-sm text-gray-300 font-mono">
            {formatTime(currentTime)} / {formatTime(data.duration)}
          </span>

          {/* Player legend */}
          <div className="flex gap-2 ml-auto flex-wrap">
            {data.players.map((p) => (
              <div key={p.player_id} className="flex items-center gap-1 text-xs text-gray-400">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
                {p.player_name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
