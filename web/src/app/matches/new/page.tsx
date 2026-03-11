"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Team {
  id: string;
  name: string;
}

export default function NewMatchPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState("");
  const [loadingTeams, setLoadingTeams] = useState(true);

  useEffect(() => {
    loadTeams();
  }, []);

  async function loadTeams() {
    try {
      // Get all schools, then get teams for the first school
      const schoolRes = await fetch(`${API}/api/v1/schools`);
      const schools = await schoolRes.json();

      if (schools.length > 0) {
        const teamRes = await fetch(`${API}/api/v1/schools/${schools[0].id}/teams`);
        const teamList = await teamRes.json();
        setTeams(teamList);
        if (teamList.length > 0) setSelectedTeam(teamList[0].id);
      }
    } catch (e) {
      console.error("Failed to load teams:", e);
    } finally {
      setLoadingTeams(false);
    }
  }

  async function getOrCreateTeam(): Promise<string> {
    // If a team is selected, use it
    if (selectedTeam) return selectedTeam;

    // Otherwise create default school + team
    let schoolId: string;
    const schoolRes = await fetch(`${API}/api/v1/schools`);
    const schools = await schoolRes.json();

    if (schools.length > 0) {
      schoolId = schools[0].id;
    } else {
      const createRes = await fetch(`${API}/api/v1/schools`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "My School", slug: "my-school" }),
      });
      if (!createRes.ok) throw new Error("Failed to create school");
      const school = await createRes.json();
      schoolId = school.id;
    }

    // Check for existing teams
    const teamRes = await fetch(`${API}/api/v1/schools/${schoolId}/teams`);
    const teamList = await teamRes.json();
    if (teamList.length > 0) return teamList[0].id;

    // Create default team
    const createTeamRes = await fetch(`${API}/api/v1/schools/${schoolId}/teams`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Default Team" }),
    });
    if (!createTeamRes.ok) throw new Error("Failed to create team");
    const team = await createTeamRes.json();
    return team.id;
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const form = new FormData(e.currentTarget);
      const teamId = await getOrCreateTeam();

      const res = await fetch(`${API}/api/v1/matches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          team_id: teamId,
          match_date: form.get("match_date") as string,
          opponent: form.get("opponent") as string || undefined,
          competition: form.get("competition") as string || undefined,
          venue: form.get("venue") as string || undefined,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const match = await res.json();
      router.push(`/matches/${match.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create match");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-6">New Match</h1>

      {error && (
        <div className="bg-red-900/30 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {teams.length > 1 && (
          <div>
            <label className="block text-sm text-gray-400 mb-1">Team</label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-emerald-500 focus:outline-none"
            >
              {teams.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
        )}

        <Field label="Match Date" name="match_date" type="date" required />
        <Field label="Opponent" name="opponent" placeholder="e.g. Menlo Park U14A" />
        <Field label="Competition" name="competition" placeholder="e.g. League Match" />
        <Field label="Venue" name="venue" placeholder="e.g. Constantiapark" />

        <button
          type="submit"
          disabled={loading || loadingTeams}
          className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 text-white py-2.5 rounded-lg font-medium transition-colors"
        >
          {loading ? "Creating..." : "Create Match"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, name, type = "text", required = false, placeholder = "" }: {
  label: string; name: string; type?: string; required?: boolean; placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1">{label}</label>
      <input
        name={name}
        type={type}
        required={required}
        placeholder={placeholder}
        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:border-emerald-500 focus:outline-none"
      />
    </div>
  );
}
