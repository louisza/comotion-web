"use client";

import { useEffect, useRef, useState } from "react";
import type { TrackData } from "@/lib/api";

const TILE_URL = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}";

const ZONE_COLORS = [
  "#6b7280", // 0: standing — gray
  "#22c55e", // 1: walking — green
  "#eab308", // 2: jogging — yellow
  "#f97316", // 3: running — orange
  "#ef4444", // 4: sprinting — red
];

const ZONE_LABELS = ["Standing", "Walking", "Jogging", "Running", "Sprinting"];

interface PlayerMapProps {
  trackData: TrackData;
  quarter: number | null;
  onQuarterChange: (q: number | null) => void;
}

export default function PlayerMap({ trackData, quarter, onQuarterChange }: PlayerMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);
  const layersRef = useRef<{ heat?: any; trail?: any; sprints?: any }>({});
  const [activeLayer, setActiveLayer] = useState<"heat" | "speed" | "both">("both");
  const [showSprints, setShowSprints] = useState(true);

  useEffect(() => {
    if (!mapRef.current || typeof window === "undefined") return;

    // Dynamic import for SSR safety
    const init = async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet/dist/leaflet.css");
      // @ts-ignore
      await import("leaflet.heat");

      if (mapInstance.current) {
        mapInstance.current.remove();
      }

      const bounds = trackData.bounds;
      if (!bounds) return;

      const map = L.map(mapRef.current!, {
        center: [bounds.center_lat, bounds.center_lng],
        zoom: 18,
        maxZoom: 21,
        zoomControl: true,
      });

      L.tileLayer(TILE_URL, {
        maxZoom: 21,
        maxNativeZoom: 20,
        attribution: "",
      }).addTo(map);

      // Fit bounds with padding
      map.fitBounds(
        [[bounds.min_lat, bounds.min_lng], [bounds.max_lat, bounds.max_lng]],
        { padding: [30, 30] }
      );

      mapInstance.current = map;
      renderLayers(L, map);
    };

    init();

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, [trackData]);

  useEffect(() => {
    if (!mapInstance.current || typeof window === "undefined") return;
    const render = async () => {
      const L = (await import("leaflet")).default;
      renderLayers(L, mapInstance.current);
    };
    render();
  }, [activeLayer, showSprints, trackData]);

  function renderLayers(L: any, map: any) {
    // Clear existing
    Object.values(layersRef.current).forEach((l: any) => {
      if (l) map.removeLayer(l);
    });
    layersRef.current = {};

    const points = trackData.points;
    if (points.length === 0) return;

    // Heatmap layer
    if (activeLayer === "heat" || activeLayer === "both") {
      const heatPoints = points.map((p) => [p.lat, p.lng, 0.5]);
      // @ts-ignore
      const heat = L.heatLayer(heatPoints, {
        radius: 15,
        blur: 20,
        maxZoom: 20,
        gradient: { 0.2: "#0000ff", 0.4: "#00ff00", 0.6: "#ffff00", 0.8: "#ff8800", 1.0: "#ff0000" },
      });
      heat.addTo(map);
      layersRef.current.heat = heat;
    }

    // Speed trail layer
    if (activeLayer === "speed" || activeLayer === "both") {
      // Build polyline segments colored by speed zone
      const trailGroup = L.layerGroup();
      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        const color = ZONE_COLORS[curr.z] || ZONE_COLORS[0];
        const weight = activeLayer === "both" ? 3 : 4;
        const opacity = curr.s === 1 ? 0.3 : 0.8; // dim stale GPS

        L.polyline(
          [[prev.lat, prev.lng], [curr.lat, curr.lng]],
          { color, weight, opacity, lineCap: "round" }
        ).addTo(trailGroup);
      }
      trailGroup.addTo(map);
      layersRef.current.trail = trailGroup;
    }

    // Sprint markers
    if (showSprints && trackData.sprints.length > 0) {
      const sprintGroup = L.layerGroup();
      trackData.sprints.forEach((s, i) => {
        // Sprint start marker
        const icon = L.divIcon({
          className: "",
          html: `<div style="background:#ef4444;color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.5)">${i + 1}</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        L.marker([s.start.lat, s.start.lng], { icon })
          .bindPopup(`<b>Sprint #${i + 1}</b><br>${s.duration}s · ${s.top_speed} km/h`)
          .addTo(sprintGroup);

        // Sprint path highlight
        L.polyline(
          [[s.start.lat, s.start.lng], [s.end.lat, s.end.lng]],
          { color: "#ef4444", weight: 6, opacity: 0.6, dashArray: "8,6" }
        ).addTo(sprintGroup);
      });
      sprintGroup.addTo(map);
      layersRef.current.sprints = sprintGroup;
    }
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
      {/* Controls bar */}
      <div className="px-4 py-3 border-b border-gray-800 flex flex-wrap items-center gap-3">
        <h3 className="text-sm font-semibold text-gray-300 mr-auto">GPS Map</h3>

        {/* Layer toggle */}
        <div className="flex bg-gray-800 rounded-lg text-xs">
          {(["heat", "speed", "both"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setActiveLayer(l)}
              className={`px-3 py-1.5 rounded-lg capitalize transition-colors ${
                activeLayer === l ? "bg-emerald-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              {l === "both" ? "Both" : l === "heat" ? "Heatmap" : "Speed Trail"}
            </button>
          ))}
        </div>

        {/* Sprint toggle */}
        <button
          onClick={() => setShowSprints(!showSprints)}
          className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
            showSprints ? "bg-red-600/30 text-red-300 border border-red-700" : "bg-gray-800 text-gray-500"
          }`}
        >
          ⚡ Sprints ({trackData.sprints.length})
        </button>

        {/* Quarter selector */}
        <div className="flex bg-gray-800 rounded-lg text-xs">
          <button
            onClick={() => onQuarterChange(null)}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              quarter === null ? "bg-emerald-600 text-white" : "text-gray-400 hover:text-white"
            }`}
          >
            Full
          </button>
          {[1, 2, 3, 4].map((q) => (
            <button
              key={q}
              onClick={() => onQuarterChange(q)}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                quarter === q ? "bg-emerald-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Q{q}
            </button>
          ))}
        </div>
      </div>

      {/* Map */}
      <div ref={mapRef} style={{ height: 500 }} />

      {/* Zone coverage bar */}
      <div className="px-4 py-3 border-t border-gray-800">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-gray-500">Speed Zones</span>
        </div>
        <div className="flex h-6 rounded overflow-hidden">
          {Object.entries(trackData.zones).map(([zone, pct], i) => (
            pct > 0 && (
              <div
                key={zone}
                style={{ width: `${pct}%`, backgroundColor: ZONE_COLORS[i] }}
                className="flex items-center justify-center text-[10px] font-bold text-white/90 min-w-[20px]"
                title={`${ZONE_LABELS[i]}: ${pct}%`}
              >
                {pct >= 5 ? `${pct.toFixed(0)}%` : ""}
              </div>
            )
          ))}
        </div>
        <div className="flex gap-3 mt-2">
          {ZONE_LABELS.map((label, i) => (
            <div key={label} className="flex items-center gap-1 text-xs text-gray-500">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ZONE_COLORS[i] }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      {/* Sprint list */}
      {trackData.sprints.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-800">
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Sprints</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {trackData.sprints.map((s, i) => (
              <div key={i} className="bg-gray-800/50 rounded px-3 py-2 text-xs">
                <span className="text-red-400 font-bold">#{i + 1}</span>
                <span className="text-gray-400 ml-2">{s.duration}s</span>
                <span className="text-white ml-2">{s.top_speed} km/h</span>
                <span className="text-gray-600 ml-2">@ {Math.floor(s.start_t / 60)}:{String(Math.floor(s.start_t % 60)).padStart(2, "0")}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
