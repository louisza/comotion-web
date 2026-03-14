"use client";

import { useEffect, useState } from "react";
import { getMatch, getMatchPlayers, getPlayerTrack, type PlayerSummary, type TrackData, type Match } from "@/lib/api";
import Link from "next/link";
import dynamic from "next/dynamic";
import { MetricTooltip } from "@/components/MetricTooltip";

// Dynamic import for leaflet (no SSR)
const PlayerMap = dynamic(() => import("@/components/PlayerMap"), { ssr: false });

export default function PlayerDetailClient({ matchId, playerId }: { matchId: string; playerId: string }) {
  const [match, setMatch] = useState<Match | null>(null);
  const [player, setPlayer] = useState<PlayerSummary | null>(null);
  const [trackData, setTrackData] = useState<TrackData | null>(null);
  const [quarter, setQuarter] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadTrack();
  }, [quarter]);

  async function loadData() {
    try {
      const [m, players] = await Promise.all([
        getMatch(matchId),
        getMatchPlayers(matchId),
      ]);
      setMatch(m);
      const p = players.find((p) => p.player_id === playerId);
      setPlayer(p || null);
      await loadTrack();
    } catch (e: any) {
      setError(e.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function loadTrack() {
    try {
      const track = await getPlayerTrack(matchId, playerId, quarter ?? undefined);
      setTrackData(track);
    } catch {
      // Track data might not be available
    }
  }

  if (loading) return <div className="text-gray-500 text-center py-12">Loading...</div>;
  if (error) return <div className="text-red-400 text-center py-12">{error}</div>;
  if (!match || !player) return <div className="text-gray-500 text-center py-12">Player not found</div>;

  const metrics = [
    { label: "Minutes Played", value: player.minutes_played?.toFixed(0), unit: "min" },
    { label: "Total Distance", value: player.total_distance_m?.toFixed(0), unit: "m" },
    { label: "Distance / Min", value: player.distance_per_min?.toFixed(0), unit: "m/min" },
    { label: "Top Speed", value: player.top_speed_kmh?.toFixed(1), unit: "km/h" },
    { label: "HSR Distance", value: player.hsr_distance_m?.toFixed(0), unit: "m" },
    { label: "Sprint Count", value: player.sprint_count?.toString(), unit: "" },
    { label: "Accelerations", value: player.accel_count?.toString(), unit: "" },
    { label: "Decelerations", value: player.decel_count?.toString(), unit: "" },
    { label: "Total Load", value: player.total_load?.toFixed(0), unit: "" },
    { label: "Load / Min", value: player.load_per_min?.toFixed(1), unit: "/min" },
  ];

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href={`/matches/${matchId}`} className="text-gray-500 hover:text-white">←</Link>
        <div>
          <h1 className="text-2xl font-bold">{player.player_name || "Player"}</h1>
          <p className="text-gray-400 text-sm">
            {match.opponent ? `vs ${match.opponent}` : "Match"} — {match.match_date}
          </p>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        {metrics.map((m) => (
          <div key={m.label} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider"><MetricTooltip label={m.label}>{m.label}</MetricTooltip></p>
            <p className="text-xl font-bold text-white mt-1">
              {m.value ?? "—"}
              {m.value && m.unit && <span className="text-sm text-gray-500 ml-1">{m.unit}</span>}
            </p>
          </div>
        ))}
      </div>

      {/* GPS Map */}
      {trackData && trackData.points.length > 0 ? (
        <PlayerMap
          trackData={trackData}
          quarter={quarter}
          onQuarterChange={setQuarter}
        />
      ) : (
        <div className="bg-gray-900 rounded-lg border border-gray-800 px-6 py-12 text-center text-gray-500">
          <p className="text-lg mb-2">🗺️ No GPS Data Available</p>
          <p className="text-sm">Upload a CSV with GPS coordinates to see the movement map</p>
        </div>
      )}

      {/* Back link */}
      <div className="mt-6">
        <Link href={`/matches/${matchId}`} className="text-emerald-400 hover:underline text-sm">
          ← Back to match overview
        </Link>
      </div>
    </div>
  );
}
