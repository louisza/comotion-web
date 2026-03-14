import { getMatch, getMatchPlayers, getMatchUploads, type Match, type PlayerSummary, type Upload } from "@/lib/api";
import { notFound } from "next/navigation";
import Link from "next/link";
import UploadSection from "./upload-section";
import MatchActions from "./match-actions";
import PlayerTable from "./player-table";
import ReplaySection from "./replay-section";

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let match: Match | undefined, players: PlayerSummary[], uploads: Upload[];

  try {
    match = await getMatch(id);
  } catch (e: any) {
    // 404 means genuinely not found; other errors (network, 500) we surface
    if (e?.message?.includes("404")) notFound();
    throw e; // let Next.js error boundary handle it
  }
  try {
    [players, uploads] = await Promise.all([
      getMatchPlayers(id),
      getMatchUploads(id),
    ]);
  } catch {
    players = [];
    uploads = [];
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
        <span className={`px-3 py-1 rounded text-xs font-medium ${
          match.status === "ready" ? "bg-emerald-900/50 text-emerald-300" :
          match.status === "processing" ? "bg-yellow-900/50 text-yellow-300" :
          match.status === "error" ? "bg-red-900/50 text-red-300" :
          "bg-gray-800 text-gray-400"
        }`}>{match.status}</span>
        <MatchActions match={match} />
      </div>

      {/* Upload section */}
      <UploadSection matchId={id} initialUploads={uploads} />

      {/* Replay */}
      <ReplaySection matchId={id} />

      {/* Player summaries */}
      {players.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 mt-6">
          <div className="px-6 py-4 border-b border-gray-800">
            <h2 className="text-lg font-semibold">Player Performance</h2>
          </div>
          <PlayerTable players={players} matchId={id} />
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
