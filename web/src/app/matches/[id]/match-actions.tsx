"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { deleteMatch, updateMatch, type Match } from "@/lib/api";

interface Props {
  match: Match;
}

export default function MatchActions({ match }: Props) {
  const router = useRouter();
  const [showEdit, setShowEdit] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    match_date: match.match_date,
    opponent: match.opponent ?? "",
    competition: match.competition ?? "",
    venue: match.venue ?? "",
  });

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateMatch(match.id, {
        match_date: form.match_date,
        opponent: form.opponent || undefined,
        competition: form.competition || undefined,
        venue: form.venue || undefined,
      });
      setSuccessMsg("Match updated successfully");
      setShowEdit(false);
      router.refresh();
    } catch (e: any) {
      setError(e.message ?? "Failed to update match");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setError(null);
    try {
      await deleteMatch(match.id);
      router.push("/?deleted=1");
    } catch (e: any) {
      setError(e.message ?? "Failed to delete match");
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  return (
    <>
      {/* Buttons */}
      <div className="flex gap-2 ml-auto items-center">
        {successMsg && (
          <span className="text-emerald-400 text-sm">{successMsg}</span>
        )}
        {error && (
          <span className="text-red-400 text-sm">{error}</span>
        )}
        <button
          onClick={() => { setShowEdit(true); setSuccessMsg(null); setError(null); }}
          className="px-3 py-1.5 text-sm rounded bg-gray-700 hover:bg-gray-600 text-white"
        >
          Edit
        </button>
        <button
          onClick={() => { setShowDeleteConfirm(true); setSuccessMsg(null); setError(null); }}
          className="px-3 py-1.5 text-sm rounded bg-red-900/60 hover:bg-red-800 text-red-300"
        >
          Delete
        </button>
      </div>

      {/* Edit Modal */}
      {showEdit && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Edit Match</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Date</label>
                <input
                  type="date"
                  value={form.match_date}
                  onChange={e => setForm(f => ({ ...f, match_date: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Opponent</label>
                <input
                  type="text"
                  value={form.opponent}
                  onChange={e => setForm(f => ({ ...f, opponent: e.target.value }))}
                  placeholder="Opponent team name"
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Competition</label>
                <input
                  type="text"
                  value={form.competition}
                  onChange={e => setForm(f => ({ ...f, competition: e.target.value }))}
                  placeholder="Competition / league"
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Venue</label>
                <input
                  type="text"
                  value={form.venue}
                  onChange={e => setForm(f => ({ ...f, venue: e.target.value }))}
                  placeholder="Venue / location"
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
                />
              </div>
            </div>
            {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
            <div className="flex gap-2 mt-5 justify-end">
              <button
                onClick={() => setShowEdit(false)}
                className="px-4 py-2 text-sm rounded bg-gray-700 hover:bg-gray-600 text-white"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.match_date}
                className="px-4 py-2 text-sm rounded bg-emerald-700 hover:bg-emerald-600 text-white disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save changes"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-sm">
            <h2 className="text-lg font-semibold mb-2">Delete Match?</h2>
            <p className="text-gray-400 text-sm mb-5">
              This will permanently delete this match and all associated data. This cannot be undone.
            </p>
            {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm rounded bg-gray-700 hover:bg-gray-600 text-white"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 text-sm rounded bg-red-700 hover:bg-red-600 text-white disabled:opacity-50"
              >
                {deleting ? "Deleting…" : "Delete match"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
