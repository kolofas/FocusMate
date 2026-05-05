import { useEffect, useMemo, useState } from "react";
import {
  AuthUser,
  clearToken,
  FocusToday,
  LifeActionTemplate,
  LifeDashboardToday,
  LifeRecentAction,
  Task,
  formatDate,
  getMe,
  getLifeDashboardToday,
  getLifeQuickActions,
  getLifeRecentActions,
  getTasks,
  getToday,
  login,
  logLifeAction,
  register,
  repeatLifeAction,
  repeatLifeShortcut,
} from "./lib/api";

type Tab = "all" | "today" | "life";
type OnboardingStep = {
  id: "life" | "repeat" | "today";
  label: string;
  done: boolean;
  ctaLabel: string;
  ctaTab: Tab;
};

function App() {
  const [tab, setTab] = useState<Tab>("all");
  const [todayVisited, setTodayVisited] = useState(false);
  const [onboardingDismissed, setOnboardingDismissed] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authPending, setAuthPending] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [today, setToday] = useState<FocusToday | null>(null);
  const [lifeDashboard, setLifeDashboard] = useState<LifeDashboardToday | null>(null);
  const [quickActions, setQuickActions] = useState<LifeActionTemplate[]>([]);
  const [recentActions, setRecentActions] = useState<LifeRecentAction[]>([]);
  const [lifePending, setLifePending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      setLoading(true);
      setError(null);
      try {
        const me = await getMe();
        if (cancelled) {
          return;
        }
        setAuthUser(me);

        const [tasksData, todayData, dashboardData, quickData, recentData] =
          await Promise.all([
            getTasks(),
            getToday(),
            getLifeDashboardToday(),
            getLifeQuickActions(),
            getLifeRecentActions(),
          ]);
        if (cancelled) {
          return;
        }
        setTasks(tasksData);
        setToday(todayData);
        setLifeDashboard(dashboardData);
        setQuickActions(quickData);
        setRecentActions(recentData);
      } catch (err) {
        if (cancelled) {
          return;
        }
        const message = err instanceof Error ? err.message : "Не удалось загрузить данные";
        if (!message.includes("401")) {
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  const todayTasks = useMemo(() => today?.items ?? [], [today]);
  const lifeCategories = useMemo(() => lifeDashboard?.categories ?? [], [lifeDashboard]);
  const onboardingSteps = useMemo<OnboardingStep[]>(() => {
    return [
      {
        id: "life",
        label: "Do one quick action in Life",
        done: recentActions.length > 0,
        ctaLabel: "Open Life",
        ctaTab: "life",
      },
      {
        id: "repeat",
        label: "Use Repeat (last/yesterday or recent)",
        done: recentActions.length >= 2,
        ctaLabel: "Open Life",
        ctaTab: "life",
      },
      {
        id: "today",
        label: "Check your Today focus list",
        done: todayVisited,
        ctaLabel: "Open Today",
        ctaTab: "today",
      },
    ];
  }, [recentActions.length, tasks.length, todayVisited]);

  const onboardingDoneCount = useMemo(
    () => onboardingSteps.filter((step) => step.done).length,
    [onboardingSteps]
  );
  const onboardingNextStep = useMemo(
    () => onboardingSteps.find((step) => !step.done) ?? null,
    [onboardingSteps]
  );
  const onboardingIsComplete = useMemo(
    () => onboardingDoneCount === onboardingSteps.length,
    [onboardingDoneCount, onboardingSteps.length]
  );
  const showOnboarding = useMemo(() => {
    if (!authUser || loading || onboardingDismissed) {
      return false;
    }
    return true;
  }, [authUser, loading, onboardingDismissed]);

  async function refreshLifeData() {
    const [dashboardData, recentData] = await Promise.all([
      getLifeDashboardToday(),
      getLifeRecentActions(),
    ]);
    setLifeDashboard(dashboardData);
    setRecentActions(recentData);
  }

  async function onQuickAction(templateId: number) {
    setLifePending(true);
    setError(null);
    try {
      await logLifeAction(templateId);
      await refreshLifeData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось записать действие");
    } finally {
      setLifePending(false);
    }
  }

  async function onRepeatAction(userActionId: number) {
    setLifePending(true);
    setError(null);
    try {
      await repeatLifeAction(userActionId);
      await refreshLifeData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось повторить действие");
    } finally {
      setLifePending(false);
    }
  }

  async function onRepeatShortcut(mode: "last" | "yesterday") {
    setLifePending(true);
    setError(null);
    try {
      await repeatLifeShortcut(mode);
      await refreshLifeData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось выполнить shortcut");
    } finally {
      setLifePending(false);
    }
  }

  async function reloadData() {
    const [tasksData, todayData, dashboardData, quickData, recentData] =
      await Promise.all([
        getTasks(),
        getToday(),
        getLifeDashboardToday(),
        getLifeQuickActions(),
        getLifeRecentActions(),
      ]);
    setTasks(tasksData);
    setToday(todayData);
    setLifeDashboard(dashboardData);
    setQuickActions(quickData);
    setRecentActions(recentData);
  }

  async function onSubmitAuth() {
    setAuthPending(true);
    setError(null);
    try {
      if (authMode === "register") {
        await register(email.trim(), password);
      }
      await login(email.trim(), password);
      const me = await getMe();
      setAuthUser(me);
      await reloadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    } finally {
      setAuthPending(false);
    }
  }

  function onLogout() {
    clearToken();
    setAuthUser(null);
    setTodayVisited(false);
    setOnboardingDismissed(false);
    setTasks([]);
    setToday(null);
    setLifeDashboard(null);
    setQuickActions([]);
    setRecentActions([]);
  }

  return (
    <main className="page">
      <section className="shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">FocusMate Web MVP</p>
            <h1>Clean Focus Board</h1>
          </div>
          {authUser ? (
            <div>
              <button className="ghost" onClick={() => window.location.reload()}>
                Refresh
              </button>
              <button className="ghost" onClick={onLogout}>
                Logout
              </button>
            </div>
          ) : null}
        </header>

        {!authUser && (
          <section className="panel">
            <h2>{authMode === "login" ? "Login" : "Register"}</h2>
            <div className="quick-actions">
              <input
                className="quick-btn"
                type="email"
                value={email}
                placeholder="email"
                onChange={(e) => setEmail(e.target.value)}
                disabled={authPending}
              />
              <input
                className="quick-btn"
                type="password"
                value={password}
                placeholder="password"
                onChange={(e) => setPassword(e.target.value)}
                disabled={authPending}
              />
              <button className="quick-btn" onClick={onSubmitAuth} disabled={authPending}>
                {authMode === "login" ? "Sign in" : "Create account"}
              </button>
              <button
                className="ghost"
                onClick={() =>
                  setAuthMode((prev) => (prev === "login" ? "register" : "login"))
                }
                disabled={authPending}
              >
                {authMode === "login" ? "Switch to register" : "Switch to login"}
              </button>
            </div>
          </section>
        )}

        {authUser && (
        <nav className="tabs" aria-label="View selector">
          <button
            className={tab === "all" ? "tab tab--active" : "tab"}
            onClick={() => setTab("all")}
          >
            All tasks
          </button>
          <button
            className={tab === "today" ? "tab tab--active" : "tab"}
            onClick={() => {
              setTab("today");
              setTodayVisited(true);
            }}
          >
            Today
          </button>
          <button
            className={tab === "life" ? "tab tab--active" : "tab"}
            onClick={() => setTab("life")}
          >
            Life
          </button>
        </nav>
        )}

        {loading && <p className="state">Загрузка...</p>}
        {error && <p className="state state--error">{error}</p>}

        {showOnboarding && (
          <section className="panel onboarding">
            <div className="onboarding__top">
              <h2>First 2 minutes</h2>
              <span className="onboarding__progress">
                {onboardingDoneCount}/{onboardingSteps.length}
              </span>
            </div>
            {!onboardingIsComplete && onboardingNextStep ? (
              <p className="onboarding__next">
                Current step: <strong>{onboardingNextStep.label}</strong>
              </p>
            ) : null}
            {!onboardingIsComplete && onboardingNextStep ? (
              <div className="quick-actions">
                <button
                  className="quick-btn"
                  onClick={() => {
                    setTab(onboardingNextStep.ctaTab);
                    if (onboardingNextStep.ctaTab === "today") {
                      setTodayVisited(true);
                    }
                  }}
                >
                  {onboardingNextStep.ctaLabel}
                </button>
              </div>
            ) : null}
            {onboardingIsComplete ? (
              <div className="onboarding__done">
                <p>Nice start. Your first-run checklist is complete.</p>
                <button className="ghost" onClick={() => setOnboardingDismissed(true)}>
                  Hide onboarding
                </button>
              </div>
            ) : null}
            <ul className="onboarding__checklist">
              {onboardingSteps.map((step) => (
                <li key={step.id} className={step.done ? "done" : ""}>
                  {step.done ? "✓" : "○"} {step.label}
                </li>
              ))}
            </ul>
          </section>
        )}

        {!!authUser && !loading && tab === "all" && (
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

        {!!authUser && !loading && tab === "today" && (
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

        {!!authUser && !loading && tab === "life" && (
          <section className="panel">
            <h2>Life today {lifeDashboard ? `• ${lifeDashboard.date}` : ""}</h2>

            <div className="life-shortcuts">
              <button
                className="ghost"
                onClick={() => onRepeatShortcut("last")}
                disabled={lifePending}
              >
                Repeat last
              </button>
              <button
                className="ghost"
                onClick={() => onRepeatShortcut("yesterday")}
                disabled={lifePending}
              >
                Repeat yesterday
              </button>
            </div>

            <div className="life-grid">
              {lifeCategories.map((category) => (
                <article key={category.category_id} className="life-card">
                  <p className="life-card__title">{category.title}</p>
                  <p className="life-card__points">{category.points} pts</p>
                </article>
              ))}
            </div>

            <h3>Quick actions</h3>
            <div className="quick-actions">
              {quickActions.map((action) => (
                <button
                  key={action.id}
                  className="quick-btn"
                  onClick={() => onQuickAction(action.id)}
                  disabled={lifePending}
                >
                  {action.title}
                </button>
              ))}
            </div>

            <h3>Recent</h3>
            <ul className="list">
              {recentActions.map((action) => (
                <li key={action.id} className="item">
                  <div className="item__main">
                    <strong>{action.title}</strong>
                    <button
                      className="ghost ghost--small"
                      onClick={() => onRepeatAction(action.id)}
                      disabled={lifePending}
                    >
                      Repeat
                    </button>
                  </div>
                  <div className="item__meta">
                    <span>category: {action.category_title ?? "-"}</span>
                    <span>points: {action.points}</span>
                    <span>{formatDate(action.happened_at)}</span>
                  </div>
                </li>
              ))}
              {recentActions.length === 0 && <li className="state">Пока нет действий</li>}
            </ul>
          </section>
        )}
      </section>
    </main>
  );
}

export default App;
