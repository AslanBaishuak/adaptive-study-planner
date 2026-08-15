export default function MasteryGrid({ items = [] }) {
  return (
    <section className="panel mastery-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Skill map</p>
          <h2>Topic mastery</h2>
        </div>
        <p className="section-note">
          Mastery combines difficulty, accuracy, and evidence from repeated attempts.
        </p>
      </div>
      <div className="mastery-grid">
        {items.map((item) => (
          <article className="mastery-card" key={item.topic}>
            <div className="mastery-title">
              <span>{item.topic}</span>
              <span>{item.mastery}%</span>
            </div>
            <div className="mastery-status">{item.status}</div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${Math.max(2, item.mastery)}%` }} />
            </div>
            <div className="mastery-meta">
              <span>{item.accuracy}% accuracy</span>
              <span>Rating {item.rating}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
