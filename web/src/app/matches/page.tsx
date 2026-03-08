import { getMatches, type Match } from "@/lib/api";
import Link from "next/link";

export default async function MatchesPage() {
  let matches: Match[] = [];
  try {
    matches = await getMatches();
  } catch {}

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">All Matches</h1>
        <Link
          href="/matches/new"
          className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + New Match
        </Link>
      </div>

      {matches.length === 0 ? (
        <div className="bg-gray-900 rounded-lg border border-gray-800 px-6 py-16 text-center">
          <p className="text-5xl mb-4">🏑</p>
          <p className="text-lg text-gray-400 mb-2">No matches yet</p>
          <p className="text-sm text-gray-600 mb-4">Create your first match to start uploading player data.</p>
          <Link href="/matches/new" className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium">
            Create Match
          </Link>
        </div>
      ) : (
        <div className="grid gap-3">
          {matches.map((m) => (
            <Link
              key={m.id}
              href={`/matches/${m.id}`}
              className="bg-gray-900 rounded-lg border border-gray-800 p-4 hover:border-gray-700 transition-colors flex items-center justify-between"
            >
              <div>
                <p className="font-medium">
                  {m.opponent ? `vs ${m.opponent}` : "Match"}{" "}
                  <span className="text-gray-500">— {m.match_date}</span>
                </p>
                <p className="text-sm text-gray-500 mt-0.5">
                  {[m.competition, m.venue].filter(Boolean).join(" · ") || "No details"}
                </p>
              </div>
              <span className={`px-2 py-0.5 rounded text-xs border ${
                m.status === "ready" ? "bg-emerald-900/50 text-emerald-300 border-emerald-800" :
                m.status === "processing" ? "bg-yellow-900/50 text-yellow-300 border-yellow-800" :
                m.status === "error" ? "bg-red-900/50 text-red-300 border-red-800" :
                "bg-gray-800 text-gray-400 border-gray-700"
              }`}>{m.status}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
