import { getMatches, type Match } from "@/lib/api";
import Link from "next/link";

export default async function Home() {
  let matches: Match[] = [];
  try {
    matches = await getMatches();
  } catch {}

  const ready = matches.filter((m) => m.status === "ready").length;
  const processing = matches.filter((m) => m.status === "processing").length;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1">Match analytics for field hockey coaches</p>
        </div>
        <Link
          href="/matches/new"
          className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + New Match
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Matches" value={matches.length} color="emerald" />
        <StatCard label="Ready" value={ready} color="emerald" />
        <StatCard label="Processing" value={processing} color="yellow" />
        <StatCard label="Version" value="v0.1.0" color="gray" />
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800">
        <div className="px-6 py-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold">Recent Matches</h2>
        </div>
        {matches.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            <p className="text-4xl mb-3">🏑</p>
            <p>No matches yet.</p>
            <Link href="/matches/new" className="text-emerald-400 hover:underline text-sm">
              Create your first match →
            </Link>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-800">
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Opponent</th>
                <th className="px-6 py-3">Competition</th>
                <th className="px-6 py-3">Venue</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m) => (
                <tr key={m.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-6 py-3">
                    <Link href={`/matches/${m.id}`} className="text-emerald-400 hover:underline">
                      {m.match_date}
                    </Link>
                  </td>
                  <td className="px-6 py-3">{m.opponent || "—"}</td>
                  <td className="px-6 py-3">{m.competition || "—"}</td>
                  <td className="px-6 py-3">{m.venue || "—"}</td>
                  <td className="px-6 py-3">
                    <StatusBadge status={m.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  const colors: Record<string, string> = {
    emerald: "text-emerald-400",
    yellow: "text-yellow-400",
    gray: "text-gray-400",
    red: "text-red-400",
  };
  return (
    <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${colors[color] || colors.gray}`}>{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    ready: "bg-emerald-900/50 text-emerald-300 border-emerald-800",
    processing: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
    error: "bg-red-900/50 text-red-300 border-red-800",
    pending: "bg-gray-800 text-gray-400 border-gray-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs border ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}
