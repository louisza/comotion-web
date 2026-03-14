"use client";
import Link from "next/link";
import type { PlayerSummary } from "@/lib/api";
import { MetricTooltip } from "@/components/MetricTooltip";

export default function PlayerTable({ players, matchId }: { players: PlayerSummary[]; matchId: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b border-gray-800">
            <th className="px-4 py-3"><MetricTooltip label="Player">Player</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Min">Min</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Dist (m)">Dist (m)</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="m/min">m/min</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Top Speed">Top Speed</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="HSR (m)">HSR (m)</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Sprints">Sprints</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Accels">Accels</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Decels">Decels</MetricTooltip></th>
            <th className="px-4 py-3 text-right"><MetricTooltip label="Load">Load</MetricTooltip></th>
          </tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr key={p.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-4 py-3 font-medium">
                <Link href={`/matches/${matchId}/players/${p.player_id}`} className="text-emerald-400 hover:underline">
                  {p.player_name || p.player_id.slice(0, 8)}
                </Link>
              </td>
              <td className="px-4 py-3 text-right">{p.minutes_played?.toFixed(0) ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.total_distance_m?.toFixed(0) ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.distance_per_min?.toFixed(0) ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.top_speed_kmh?.toFixed(1) ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.hsr_distance_m?.toFixed(0) ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.sprint_count ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.accel_count ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.decel_count ?? "—"}</td>
              <td className="px-4 py-3 text-right">{p.total_load?.toFixed(0) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
