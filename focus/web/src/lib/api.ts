export type TaskStatus = "inbox" | "planned" | "done" | "snoozed";

export type Task = {
  id: number;
  title: string;
  description: string | null;
  source: string;
  status: TaskStatus;
  deadline: string | null;
  reminder_at: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
};

export type FocusItem = {
  rank: number;
  score: number;
  task: Task;
};

export type FocusToday = {
  date: string;
  items: FocusItem[];
};

export type LifeActionTemplate = {
  id: number;
  category_id: number | null;
  slug: string;
  title: string;
  default_points: number;
  default_duration_min: number | null;
  is_active: boolean;
};

export type LifeRecentAction = {
  id: number;
  user_id: number | null;
  template_id: number | null;
  category_id: number | null;
  category_slug: string | null;
  category_title: string | null;
  title: string;
  points: number;
  duration_min: number | null;
  happened_at: string;
};

export type LifeDashboardCategory = {
  category_id: number;
  slug: string;
  title: string;
  points: number;
};

export type LifeDashboardToday = {
  date: string;
  total_points: number;
  categories: LifeDashboardCategory[];
};

export type AuthUser = {
  id: number;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  telegram_user_id: number | null;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const TOKEN_KEY = "focusmate_token";

function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  const body = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const message = body?.error?.message ?? `Request failed: ${resp.status}`;
    throw new Error(message);
  }

  return body as T;
}

export function getTasks(): Promise<Task[]> {
  return request<Task[]>("/tasks/");
}

export function getToday(): Promise<FocusToday> {
  return request<FocusToday>("/focus/today");
}

export function getLifeQuickActions(): Promise<LifeActionTemplate[]> {
  return request<LifeActionTemplate[]>("/life/actions/quick");
}

export function getLifeRecentActions(limit = 8): Promise<LifeRecentAction[]> {
  return request<LifeRecentAction[]>(`/life/actions/recent?limit=${limit}`);
}

export function getLifeDashboardToday(): Promise<LifeDashboardToday> {
  return request<LifeDashboardToday>("/life/dashboard/today");
}

export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const resp = await fetch(`${API_BASE}/auth/jwt/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok || !data?.access_token) {
    const message = data?.error?.message ?? "Login failed";
    throw new Error(message);
  }
  setToken(data.access_token);
}

export async function register(email: string, password: string): Promise<void> {
  await request<AuthUser>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function getMe(): Promise<AuthUser> {
  return request<AuthUser>("/users/me");
}

export function logLifeAction(templateId: number): Promise<{
  user_action_id: number;
}> {
  return request("/life/actions/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template_id: templateId }),
  });
}

export function repeatLifeAction(userActionId: number): Promise<{
  user_action_id: number;
}> {
  return request("/life/actions/repeat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_action_id: userActionId }),
  });
}

export function repeatLifeShortcut(mode: "last" | "yesterday"): Promise<{
  user_action_id: number;
}> {
  return request("/life/actions/repeat-shortcut", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
}

export function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }

  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(dt);
}
