"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NewMatchPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const form = new FormData(e.currentTarget);
    const body = {
      team_id: form.get("team_id") as string,
      match_date: form.get("match_date") as string,
      opponent: form.get("opponent") as string || undefined,
      competition: form.get("competition") as string || undefined,
      venue: form.get("venue") as string || undefined,
    };

    // If no team_id, create a default org + team first
    if (!body.team_id) {
      try {
        const orgRes = await fetch(`${API}/api/v1/organizations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: "My Organization" }),
        });
        const org = await orgRes.json();
        const teamRes = await fetch(`${API}/api/v1/organizations/${org.id}/teams`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: "My Team" }),
        });
        const team = await teamRes.json();
        body.team_id = team.id;
      } catch (err) {
        setError("Failed to create default team");
        setLoading(false);
        return;
      }
    }

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
        <input type="hidden" name="team_id" value="" />

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
