import { getMatch, getMatchPlayers, type PlayerSummary } from "@/lib/api";
import { notFound } from "next/navigation";
import Link from "next/link";

export default async function PlayerDetailPage({
  params,
}: {
  params: Promise<{ id: string; playerId: string }>;
}) {
  const { id, playerId } = await params;
  let match, players: PlayerSummary[];

  try {
    [match, players] = await Promise.all([getMatch(id), getMatchPlayers(id)]);
  } catch {
    notFound();
  }

  const player = players.find((p) => p.player_id === playerId);
  if (!player) notFound();

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
    { label: "Peak 1min", value: player.peak_1min_intensity?.toFixed(1), unit: "" },
    { label: "Peak 3min", value: player.peak_3min_intensity?.toFixed(1), unit: "" },
    { label: "Peak 5min", value: player.peak_5min_intensity?.toFixed(1), unit: "" },
    { label: "Impacts", value: player.impact_count?.toString(), unit: "" },
  ];

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href={`/matches/${id}`} className="text-gray-500 hover:text-white">←</Link>
        <div>
          <h1 className="text-2xl font-bold">Player Card</h1>
          <p className="text-gray-400 text-sm">
            {match.opponent ? `vs ${match.opponent}` : "Match"} — {match.match_date}
          </p>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
        {metrics.map((m) => (
          <div key={m.label} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider">{m.label}</p>
            <p className="text-xl font-bold text-white mt-1">
              {m.value ?? "—"}
              {m.value && m.unit && <span className="text-sm text-gray-500 ml-1">{m.unit}</span>}
            </p>
          </div>
        ))}
      </div>

      {/* Intensity bar */}
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 mb-6">
        <h3 className="text-sm text-gray-400 mb-3">Load Distribution</h3>
        <div className="flex gap-1 h-8">
          {player.total_load && player.minutes_played ? (
            Array.from({ length: Math.min(Math.ceil(player.minutes_played), 60) }, (_, i) => {
              const intensity = Math.random() * 0.7 + 0.3; // Placeholder — need quarter data
              return (
                <div
                  key={i}
                  className="flex-1 rounded-sm"
                  style={{
                    backgroundColor: `hsl(${120 - intensity * 120}, 70%, ${30 + intensity * 20}%)`,
                  }}
                />
              );
            })
          ) : (
            <p className="text-gray-600 text-sm">No load data available</p>
          )}
        </div>
        <div className="flex justify-between text-xs text-gray-600 mt-1">
          <span>Start</span>
          <span>End</span>
        </div>
      </div>

      {/* Back link */}
      <Link href={`/matches/${id}`} className="text-emerald-400 hover:underline text-sm">
        ← Back to match overview
      </Link>
    </div>
  );
}
