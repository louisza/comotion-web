"use client";

import { useEffect, useState } from "react";
import {
  getSchools, getAllTeams, getTeams, createTeam, updateTeam, deleteTeam,
  School, Team
} from "@/lib/api";

type FormMode = "add" | "edit" | null;

export default function TeamsPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [filterSchool, setFilterSchool] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [mode, setMode] = useState<FormMode>(null);
  const [editTarget, setEditTarget] = useState<Team | null>(null);

  const [formName, setFormName] = useState("");
  const [formSchoolId, setFormSchoolId] = useState("");
  const [formAgeGroup, setFormAgeGroup] = useState("");
  const [formGender, setFormGender] = useState("");
  const [formSeasonYear, setFormSeasonYear] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<Team | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const [schoolsData, teamsData] = await Promise.all([getSchools(), getAllTeams()]);
      setSchools(schoolsData);
      setTeams(teamsData);
    } catch (e: any) {
      setError(e.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filteredTeams = filterSchool === "all"
    ? teams
    : teams.filter(t => t.school_id === filterSchool);

  const schoolName = (id: string) => schools.find(s => s.id === id)?.name ?? "—";

  const openAdd = () => {
    setMode("add");
    setEditTarget(null);
    setFormName(""); setFormSchoolId(filterSchool !== "all" ? filterSchool : schools[0]?.id ?? "");
    setFormAgeGroup(""); setFormGender(""); setFormSeasonYear(String(new Date().getFullYear()));
    setFormError(null);
  };

  const openEdit = (team: Team) => {
    setMode("edit");
    setEditTarget(team);
    setFormName(team.name);
    setFormSchoolId(team.school_id);
    setFormAgeGroup(team.age_group || "");
    setFormGender(team.gender || "");
    setFormSeasonYear(team.season_year ? String(team.season_year) : "");
    setFormError(null);
  };

  const closeForm = () => { setMode(null); setEditTarget(null); setFormError(null); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) { setFormError("Name is required"); return; }
    if (!formSchoolId) { setFormError("Please select a school"); return; }
    setSaving(true);
    setFormError(null);
    const payload = {
      name: formName.trim(),
      age_group: formAgeGroup.trim() || undefined,
      gender: formGender || undefined,
      season_year: formSeasonYear ? parseInt(formSeasonYear) : undefined,
    };
    try {
      if (mode === "add") {
        await createTeam(formSchoolId, payload);
        setSuccess("Team created ✓");
      } else if (mode === "edit" && editTarget) {
        await updateTeam(editTarget.school_id, editTarget.id, payload);
        setSuccess("Team updated ✓");
      }
      closeForm();
      await load();
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: any) {
      setFormError(e.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteTeam(deleteTarget.school_id, deleteTarget.id);
      setSuccess("Team deleted ✓");
      setDeleteTarget(null);
      await load();
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: any) {
      const msg = e.message || "Failed to delete";
      if (msg.includes("409") || msg.includes("match")) {
        setError(`⚠️ Cannot delete team "${deleteTarget.name}": it has matches. Delete matches first.`);
      } else {
        setError(msg);
      }
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Teams</h2>
          <select
            value={filterSchool}
            onChange={e => setFilterSchool(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Schools</option>
            {schools.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={openAdd}
          disabled={schools.length === 0}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          title={schools.length === 0 ? "Add a school first" : undefined}
        >
          + Add Team
        </button>
      </div>

      {schools.length === 0 && !loading && (
        <div className="mb-4 p-3 bg-amber-900/30 border border-amber-700 rounded-lg text-amber-300 text-sm">
          ⚠️ No schools found. <a href="/settings/schools" className="underline hover:text-amber-200">Add a school first</a> before creating teams.
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-emerald-900/50 border border-emerald-700 rounded-lg text-emerald-300 text-sm">{success}</div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 ml-4">✕</button>
        </div>
      )}

      {/* Team Form Modal */}
      {mode && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">
              {mode === "add" ? "Add Team" : "Edit Team"}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">School *</label>
                <select
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={formSchoolId}
                  onChange={e => setFormSchoolId(e.target.value)}
                  required
                >
                  <option value="">Select school…</option>
                  {schools.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Team Name *</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={formName}
                  onChange={e => setFormName(e.target.value)}
                  placeholder="e.g. U16 Girls Hockey"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Age Group</label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                    value={formAgeGroup}
                    onChange={e => setFormAgeGroup(e.target.value)}
                    placeholder="U16, U19, Open…"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Gender</label>
                  <select
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                    value={formGender}
                    onChange={e => setFormGender(e.target.value)}
                  >
                    <option value="">—</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="Mixed">Mixed</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Season Year</label>
                <input
                  type="number"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={formSeasonYear}
                  onChange={e => setFormSeasonYear(e.target.value)}
                  placeholder={String(new Date().getFullYear())}
                  min="2020" max="2030"
                />
              </div>
              {formError && (
                <div className="p-2 bg-red-900/40 border border-red-700 rounded text-red-300 text-sm">{formError}</div>
              )}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  {saving ? "Saving…" : mode === "add" ? "Create Team" : "Save Changes"}
                </button>
                <button
                  type="button"
                  onClick={closeForm}
                  className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm">
            <h3 className="text-lg font-semibold text-white mb-2">Delete Team</h3>
            <p className="text-gray-400 text-sm mb-1">
              Are you sure you want to delete <span className="text-white font-medium">{deleteTarget.name}</span>?
            </p>
            {(deleteTarget.match_count ?? 0) > 0 && (
              <p className="text-amber-400 text-sm mt-2">
                ⚠️ This team has {deleteTarget.match_count} match(es). You must delete matches first.
              </p>
            )}
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 py-2 bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Teams List */}
      {loading ? (
        <div className="text-gray-400 text-sm">Loading teams…</div>
      ) : filteredTeams.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-3">👥</div>
          <p className="text-sm">No teams yet. Add your first team to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredTeams.map(team => (
            <div key={team.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
              <div>
                <div className="font-medium text-white">{team.name}</div>
                <div className="text-sm text-gray-500 mt-0.5 flex flex-wrap gap-x-3">
                  <span className="text-gray-400">{schoolName(team.school_id)}</span>
                  {team.age_group && <span>{team.age_group}</span>}
                  {team.gender && <span>{team.gender === "M" ? "Male" : team.gender === "F" ? "Female" : "Mixed"}</span>}
                  {team.season_year && <span>{team.season_year}</span>}
                  <span className="text-gray-600">{team.match_count ?? 0} match{(team.match_count ?? 0) !== 1 ? "es" : ""}</span>
                  {!team.is_active && <span className="text-amber-600">Inactive</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => openEdit(team)}
                  className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => setDeleteTarget(team)}
                  className="px-3 py-1.5 text-xs bg-red-900/40 hover:bg-red-900/60 text-red-400 rounded-lg transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
