import { useEffect, useMemo, useState } from "react";
import { FocusToday, Task, formatDate, getTasks, getToday } from "./lib/api";

type Tab = "all" | "today";

function App() {
  const [tab, setTab] = useState<Tab>("all");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [today, setToday] = useState<FocusToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [tasksData, todayData] = await Promise.all([getTasks(), getToday()]);
        if (cancelled) {
          return;
        }
        setTasks(tasksData);
        setToday(todayData);
      } catch (err) {
        if (cancelled) {
          return;
        }
        setError(err instanceof Error ? err.message : "Не удалось загрузить данные");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const todayTasks = useMemo(() => today?.items ?? [], [today]);

  return (
    <main className="page">
      <section className="shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">FocusMate Web MVP</p>
            <h1>Clean Focus Board</h1>
          </div>
          <button className="ghost" onClick={() => window.location.reload()}>
            Refresh
          </button>
        </header>

        <nav className="tabs" aria-label="View selector">
          <button
            className={tab === "all" ? "tab tab--active" : "tab"}
            onClick={() => setTab("all")}
          >
            All tasks
          </button>
          <button
            className={tab === "today" ? "tab tab--active" : "tab"}
            onClick={() => setTab("today")}
          >
            Today
          </button>
        </nav>

        {loading && <p className="state">Загрузка...</p>}
        {error && <p className="state state--error">{error}</p>}

        {!loading && !error && tab === "all" && (
          <section className="panel">
            <h2>All tasks</h2>
            <ul className="list">
              {tasks.map((task) => (
                <li key={task.id} className="item">
                  <div className="item__main">
                    <span className={`badge badge--${task.status}`}>{task.status}</span>
                    <strong>[id:{task.id}] {task.title}</strong>
                  </div>
                  <div className="item__meta">
                    <span>deadline: {formatDate(task.deadline)}</span>
                    <span>reminder: {formatDate(task.reminder_at)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {!loading && !error && tab === "today" && (
          <section className="panel">
            <h2>Today {today ? `• ${today.date}` : ""}</h2>
            <ul className="list">
              {todayTasks.map((entry) => (
                <li key={entry.task.id} className="item">
                  <div className="item__main">
                    <span className="rank">#{entry.rank}</span>
                    <strong>[id:{entry.task.id}] {entry.task.title}</strong>
                  </div>
                  <div className="item__meta">
                    <span>score: {entry.score}</span>
                    <span>deadline: {formatDate(entry.task.deadline)}</span>
                    <span>reminder: {formatDate(entry.task.reminder_at)}</span>
                  </div>
                </li>
              ))}
              {todayTasks.length === 0 && <li className="state">На сегодня задач нет</li>}
            </ul>
          </section>
        )}
      </section>
    </main>
  );
}

export default App;
