const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Match {
  id: string;
  team_id: string;
  match_date: string;
  opponent: string | null;
  competition: string | null;
  venue: string | null;
  status: string;
  created_at: string;
}

export interface PlayerSummary {
  id: string;
  match_id: string;
  player_id: string;
  player_name: string | null;
  minutes_played: number | null;
  total_distance_m: number | null;
  distance_per_min: number | null;
  top_speed_kmh: number | null;
  hsr_distance_m: number | null;
  sprint_count: number | null;
  accel_count: number | null;
  decel_count: number | null;
  total_load: number | null;
  load_per_min: number | null;
  peak_1min_intensity: number | null;
  peak_3min_intensity: number | null;
  peak_5min_intensity: number | null;
  impact_count: number | null;
  movement_count: number | null;
}

export interface Upload {
  id: string;
  match_id: string;
  player_id: string | null;
  filename: string;
  status: string;
  row_count: number | null;
  quality_flags: Record<string, any> | null;
  error_message: string | null;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  created_at: string;
}

export interface Team {
  id: string;
  org_id: string;
  name: string;
  age_group: string | null;
  created_at: string;
}

export interface Player {
  id: string;
  team_id: string;
  name: string;
  jersey_number: number | null;
  position: string | null;
  created_at: string;
}

async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    cache: "no-store",
    headers: { ...opts?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Matches
export const getMatches = (teamId?: string) =>
  apiFetch<Match[]>(`/api/v1/matches${teamId ? `?team_id=${teamId}` : ""}`);

export const getMatch = (id: string) =>
  apiFetch<Match>(`/api/v1/matches/${id}`);

export const createMatch = (data: { team_id: string; match_date: string; opponent?: string; competition?: string; venue?: string }) =>
  apiFetch<Match>("/api/v1/matches", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const deleteMatch = (id: string) =>
  apiFetch<void>(`/api/v1/matches/${id}`, { method: "DELETE" });

// Match players
export const getMatchPlayers = (matchId: string) =>
  apiFetch<PlayerSummary[]>(`/api/v1/matches/${matchId}/players`);

// Uploads
export const getMatchUploads = (matchId: string) =>
  apiFetch<Upload[]>(`/api/v1/matches/${matchId}/uploads`);

export const uploadCSV = (matchId: string, file: File, playerId?: string) => {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams();
  if (playerId) params.set("player_id", playerId);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<Upload>(`/api/v1/matches/${matchId}/upload${qs}`, {
    method: "POST",
    body: form,
  });
};

// Organizations
export const getOrgs = () => apiFetch<Organization[]>("/api/v1/schools");
export const createOrg = (name: string) =>
  apiFetch<Organization>("/api/v1/schools", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });

// Teams
export const getTeams = (orgId: string) =>
  apiFetch<Team[]>(`/api/v1/schools/${orgId}/teams`);
export const createTeam = (orgId: string, name: string, ageGroup?: string) =>
  apiFetch<Team>(`/api/v1/schools/${orgId}/teams`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, age_group: ageGroup }),
  });

// Players
export const getPlayers = (teamId: string) =>
  apiFetch<Player[]>(`/api/v1/teams/${teamId}/players`);
export const createPlayer = (teamId: string, name: string, jerseyNumber?: number, position?: string) =>
  apiFetch<Player>(`/api/v1/teams/${teamId}/players`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, jersey_number: jerseyNumber, position }),
  });

// Track data
export interface TrackPoint {
  t: number;
  lat: number;
  lng: number;
  spd: number;
  z: number;  // speed zone: 0=stand, 1=walk, 2=jog, 3=run, 4=sprint
  s: number;  // stale flag
}

export interface Sprint {
  start_t: number;
  end_t: number;
  duration: number;
  top_speed: number;
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
}

export interface TrackData {
  points: TrackPoint[];
  sprints: Sprint[];
  zones: { standing: number; walking: number; jogging: number; running: number; sprinting: number };
  bounds: { min_lat: number; max_lat: number; min_lng: number; max_lng: number; center_lat: number; center_lng: number } | null;
  total_duration: number;
  point_count: number;
}

export const getPlayerTrack = (matchId: string, playerId: string, quarter?: number) => {
  const params = quarter ? `?quarter=${quarter}` : "";
  return apiFetch<TrackData>(`/api/v1/matches/${matchId}/players/${playerId}/track${params}`);
};
