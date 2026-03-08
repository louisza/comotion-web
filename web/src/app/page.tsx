const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getMatches() {
  try {
    const res = await fetch(`${API_URL}/api/v1/matches`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function Home() {
  const matches = await getMatches();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-400 mb-8">Welcome to Comotion. Upload match data and view player analytics.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <p className="text-sm text-gray-500">Total Matches</p>
          <p className="text-3xl font-bold text-emerald-400">{matches.length}</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <p className="text-sm text-gray-500">Status</p>
          <p className="text-3xl font-bold text-emerald-400">Online</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <p className="text-sm text-gray-500">Version</p>
          <p className="text-3xl font-bold text-gray-400">v0.1.0</p>
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
        <h2 className="text-xl font-semibold mb-4">Recent Matches</h2>
        {matches.length === 0 ? (
          <p className="text-gray-500">No matches yet. Create a match and upload CSV data to get started.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-800">
                <th className="pb-2">Date</th>
                <th className="pb-2">Opponent</th>
                <th className="pb-2">Competition</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m: any) => (
                <tr key={m.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-2">{m.match_date}</td>
                  <td className="py-2">{m.opponent || "—"}</td>
                  <td className="py-2">{m.competition || "—"}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      m.status === "ready" ? "bg-emerald-900 text-emerald-300" :
                      m.status === "processing" ? "bg-yellow-900 text-yellow-300" :
                      "bg-gray-800 text-gray-400"
                    }`}>{m.status}</span>
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
