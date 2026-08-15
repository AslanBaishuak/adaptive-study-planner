export default function Header({ health }) {
  const online = Boolean(health);
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Adaptive learning workspace</p>
        <h1>Study smarter, one session at a time.</h1>
        <p className="subtitle">
          Your difficulty, review queue, and weekly plan update from your real performance.
          Core planning runs locally for free.
        </p>
      </div>
      <div className="status-stack">
        <span className={`status-pill ${online ? "" : "error"}`}>
          {online ? "Local engine online" : "Connecting"}
        </span>
        <span className="status-pill secondary">
          {health?.ai_enabled ? `Optional AI: ${health.ai_model}` : "Optional AI disabled"}
        </span>
      </div>
    </header>
  );
}
