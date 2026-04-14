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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
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
