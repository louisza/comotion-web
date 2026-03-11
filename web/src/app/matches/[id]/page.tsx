import { getMatch, getMatchPlayers, getMatchUploads, type PlayerSummary, type Upload } from "@/lib/api";
import { notFound } from "next/navigation";
import Link from "next/link";
import UploadSection from "./upload-section";

export const dynamic = "force-dynamic";

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let match;
  let players: PlayerSummary[] = [];
  let uploads: Upload[] = [];

  try {
    match = await getMatch(id);
  } catch {
    notFound();
  }

  try {
    [players, uploads] = await Promise.all([
      getMatchPlayers(id).catch(() => [] as PlayerSummary[]),
      getMatchUploads(id).catch(() => [] as Upload[]),
    ]);
  } catch {
    // Non-fatal — page still renders with match info
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/" className="text-gray-500 hover:text-white">←</Link>
        <div>
          <h1 className="text-2xl font-bold">
            {match.opponent ? `vs ${match.opponent}` : "Match"} — {match.match_date}
          </h1>
          <p className="text-gray-400 text-sm">
            {match.competition || ""} {match.venue ? `· ${match.venue}` : ""}
          </p>
        </div>
        <span className={`ml-auto px-3 py-1 rounded text-xs font-medium ${
          match.status === "ready" ? "bg-emerald-900/50 text-emerald-300" :
          match.status === "processing" ? "bg-yellow-900/50 text-yellow-300" :
          match.status === "error" ? "bg-red-900/50 text-red-300" :
          "bg-gray-800 text-gray-400"
        }`}>{match.status}</span>
      </div>

      {/* Upload section */}
      <UploadSection matchId={id} initialUploads={uploads} />

      {/* Player summaries */}
      {players.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 mt-6">
          <div className="px-6 py-4 border-b border-gray-800">
            <h2 className="text-lg font-semibold">Player Performance</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-800">
                  <th className="px-4 py-3">Player</th>
                  <th className="px-4 py-3 text-right">Min</th>
                  <th className="px-4 py-3 text-right">Dist (m)</th>
                  <th className="px-4 py-3 text-right">m/min</th>
                  <th className="px-4 py-3 text-right">Top Speed</th>
                  <th className="px-4 py-3 text-right">HSR (m)</th>
                  <th className="px-4 py-3 text-right">Sprints</th>
                  <th className="px-4 py-3 text-right">Accels</th>
                  <th className="px-4 py-3 text-right">Decels</th>
                  <th className="px-4 py-3 text-right">Load</th>
                </tr>
              </thead>
              <tbody>
                {players.map((p) => (
                  <tr key={p.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="px-4 py-3 font-medium">
                      <Link href={`/matches/${id}/players/${p.player_id}`} className="text-emerald-400 hover:underline">
                        {p.player_id.slice(0, 8)}
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
        </div>
      )}

      {players.length === 0 && uploads.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 mt-6 px-6 py-8 text-center text-gray-500">
          <p>Processing uploads... Refresh to see player data.</p>
        </div>
      )}
    </div>
  );
}
