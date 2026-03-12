"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getOrgs, getTeams, type Organization, type Team } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NewMatchPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState("");
  const [selectedTeamId, setSelectedTeamId] = useState("");

  // Load orgs on mount
  useEffect(() => {
    getOrgs()
      .then((data) => {
        setOrgs(data);
        if (data.length === 1) {
          setSelectedOrgId(data[0].id);
        }
      })
      .catch(() => {});
  }, []);

  // Load teams when org changes
  useEffect(() => {
    if (!selectedOrgId) {
      setTeams([]);
      setSelectedTeamId("");
      return;
    }
    getTeams(selectedOrgId)
      .then((data) => {
        setTeams(data);
        if (data.length === 1) setSelectedTeamId(data[0].id);
        else setSelectedTeamId("");
      })
      .catch(() => {});
  }, [selectedOrgId]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const form = new FormData(e.currentTarget);
    let teamId = selectedTeamId;

    // Auto-create org + team if none exist
    if (!teamId) {
      try {
        const slug = `school-${Date.now()}`;
        const orgRes = await fetch(`${API}/api/v1/schools`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: "My School", slug }),
        });
        if (!orgRes.ok) {
          const txt = await orgRes.text();
          throw new Error(`Failed to create school: ${txt}`);
        }
        const org = await orgRes.json();
        const teamRes = await fetch(`${API}/api/v1/schools/${org.id}/teams`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: "My Team" }),
        });
        if (!teamRes.ok) {
          const txt = await teamRes.text();
          throw new Error(`Failed to create team: ${txt}`);
        }
        const team = await teamRes.json();
        teamId = team.id;
      } catch (err: any) {
        setError(err.message || "Failed to create default team");
        setLoading(false);
        return;
      }
    }

    const body = {
      team_id: teamId,
      match_date: form.get("match_date") as string,
      opponent: (form.get("opponent") as string) || undefined,
      competition: (form.get("competition") as string) || undefined,
      venue: (form.get("venue") as string) || undefined,
    };

    try {
      const res = await fetch(`${API}/api/v1/matches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
        {/* Team selector — only shown if orgs/teams exist */}
        {orgs.length > 0 && (
          <div>
            <label className="block text-sm text-gray-400 mb-1">School / Organisation</label>
            <select
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">— select school —</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
        )}

        {teams.length > 0 && (
          <div>
            <label className="block text-sm text-gray-400 mb-1">Team</label>
            <select
              value={selectedTeamId}
              onChange={(e) => setSelectedTeamId(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="">— select team —</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>{t.name}{t.age_group ? ` (${t.age_group})` : ""}</option>
              ))}
            </select>
          </div>
        )}

        {orgs.length === 0 && (
          <p className="text-xs text-gray-500">No schools/teams found — a default one will be created automatically.</p>
        )}

        <Field label="Match Date" name="match_date" type="date" required />
        <Field label="Opponent" name="opponent" placeholder="e.g. Menlo Park U14A" />
        <Field label="Competition" name="competition" placeholder="e.g. League Match" />
        <Field label="Venue" name="venue" placeholder="e.g. Constantiapark" />

        <button
          type="submit"
          disabled={loading}
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
