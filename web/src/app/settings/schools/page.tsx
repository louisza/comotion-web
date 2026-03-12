"use client";

import { useEffect, useState } from "react";
import { getSchools, createSchool, updateSchool, deleteSchool, School } from "@/lib/api";

type FormMode = "add" | "edit" | null;

export default function SchoolsPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [mode, setMode] = useState<FormMode>(null);
  const [editTarget, setEditTarget] = useState<School | null>(null);

  const [formName, setFormName] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [formProvince, setFormProvince] = useState("");
  const [formLogoUrl, setFormLogoUrl] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<School | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSchools();
      setSchools(data);
    } catch (e: any) {
      setError(e.message || "Failed to load schools");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openAdd = () => {
    setMode("add");
    setEditTarget(null);
    setFormName(""); setFormSlug(""); setFormProvince(""); setFormLogoUrl("");
    setFormError(null);
  };

  const openEdit = (school: School) => {
    setMode("edit");
    setEditTarget(school);
    setFormName(school.name);
    setFormSlug(school.slug);
    setFormProvince(school.province || "");
    setFormLogoUrl(school.logo_url || "");
    setFormError(null);
  };

  const closeForm = () => { setMode(null); setEditTarget(null); setFormError(null); };

  const autoSlug = (name: string) =>
    name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const handleNameChange = (v: string) => {
    setFormName(v);
    if (mode === "add") setFormSlug(autoSlug(v));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) { setFormError("Name is required"); return; }
    if (!formSlug.trim()) { setFormError("Slug is required"); return; }
    if (!/^[a-z0-9-]+$/.test(formSlug)) { setFormError("Slug: lowercase letters, numbers, hyphens only"); return; }
    setSaving(true);
    setFormError(null);
    try {
      if (mode === "add") {
        await createSchool({ name: formName.trim(), slug: formSlug.trim(), province: formProvince.trim() || undefined, logo_url: formLogoUrl.trim() || undefined });
        setSuccess("School created ✓");
      } else if (mode === "edit" && editTarget) {
        await updateSchool(editTarget.id, { name: formName.trim(), slug: formSlug.trim(), province: formProvince.trim() || undefined, logo_url: formLogoUrl.trim() || undefined });
        setSuccess("School updated ✓");
      }
      closeForm();
      await load();
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: any) {
      const msg = e.message || "Failed to save";
      setFormError(msg.includes("409") || msg.includes("slug already") ? "Slug already in use — choose a different one" : msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteSchool(deleteTarget.id);
      setSuccess("School deleted ✓");
      setDeleteTarget(null);
      await load();
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: any) {
      const msg = e.message || "Failed to delete";
      if (msg.includes("409") || msg.includes("match")) {
        setError("⚠️ Cannot delete: this school has matches. Delete matches first.");
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
        <h2 className="text-lg font-semibold text-white">Schools</h2>
        <button
          onClick={openAdd}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          + Add School
        </button>
      </div>

      {success && (
        <div className="mb-4 p-3 bg-emerald-900/50 border border-emerald-700 rounded-lg text-emerald-300 text-sm">{success}</div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 ml-4">✕</button>
        </div>
      )}

      {/* School Form Modal */}
      {mode && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">
              {mode === "add" ? "Add School" : "Edit School"}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">School Name *</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={formName}
                  onChange={e => handleNameChange(e.target.value)}
                  placeholder="e.g. Menlopark High School"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Slug * <span className="text-gray-600">(URL-friendly, no spaces)</span></label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500 font-mono"
                  value={formSlug}
                  onChange={e => setFormSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
                  placeholder="e.g. menlopark"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Province</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={formProvince}
                  onChange={e => setFormProvince(e.target.value)}
                  placeholder="e.g. Gauteng"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Logo URL</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  value={formLogoUrl}
                  onChange={e => setFormLogoUrl(e.target.value)}
                  placeholder="https://..."
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
                  {saving ? "Saving…" : mode === "add" ? "Create School" : "Save Changes"}
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
            <h3 className="text-lg font-semibold text-white mb-2">Delete School</h3>
            <p className="text-gray-400 text-sm mb-1">
              Are you sure you want to delete <span className="text-white font-medium">{deleteTarget.name}</span>?
            </p>
            {(deleteTarget.team_count ?? 0) > 0 && (
              <p className="text-amber-400 text-sm mb-3">
                ⚠️ This school has {deleteTarget.team_count} team(s). All teams and their players will be deleted. Matches must be deleted first.
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

      {/* Schools List */}
      {loading ? (
        <div className="text-gray-400 text-sm">Loading schools…</div>
      ) : schools.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-3">🏫</div>
          <p className="text-sm">No schools yet. Add your first school to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {schools.map(school => (
            <div key={school.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
              <div>
                <div className="font-medium text-white">{school.name}</div>
                <div className="text-sm text-gray-500 mt-0.5">
                  <span className="font-mono text-xs text-gray-600 mr-3">{school.slug}</span>
                  {school.province && <span className="mr-3">{school.province}</span>}
                  <span className="text-gray-600">{school.team_count ?? 0} team{(school.team_count ?? 0) !== 1 ? "s" : ""}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => openEdit(school)}
                  className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => setDeleteTarget(school)}
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
