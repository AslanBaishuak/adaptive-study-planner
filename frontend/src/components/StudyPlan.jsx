export default function StudyPlan({ plan, days, minutes, onDaysChange, onMinutesChange, onRefresh, loading }) {
  return (
    <article className="panel plan-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Adaptive schedule</p>
          <h2>Your study plan</h2>
        </div>
        <span className="local-badge">No AI tokens</span>
      </div>

      <div className="plan-controls">
        <label className="select-control">
          <span>Days</span>
          <select value={days} onChange={(event) => onDaysChange(Number(event.target.value))}>
            {[5, 7, 10, 14].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label className="select-control">
          <span>Minutes/day</span>
          <select value={minutes} onChange={(event) => onMinutesChange(Number(event.target.value))}>
            {[15, 20, 30, 45].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <button className="secondary-button" type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "Building…" : "Rebuild plan"}
        </button>
      </div>

      <p className="plan-reason">{plan?.reason || "Building a balanced diagnostic plan…"}</p>
      <div className="plan-list">
        {plan?.sessions?.map((session) => (
          <article className="plan-day" key={session.day}>
            <div className="day-number">Day {session.day}</div>
            <div>
              <h3>{session.focus_topic} · {session.minutes} minutes</h3>
              <p>{session.goal}</p>
              <ul className="plan-tasks">
                {session.tasks.map((task) => (
                  <li key={`${session.day}-${task.label}`}>
                    {task.label}: {task.detail} ({task.minutes} min)
                  </li>
                ))}
              </ul>
            </div>
          </article>
        )) || <p className="loading">Building your plan locally…</p>}
      </div>
    </article>
  );
}
