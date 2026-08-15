export default function ReviewQueue({ items = [] }) {
  return (
    <article className="panel review-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Spaced review</p>
          <h2>Retry queue</h2>
        </div>
        <span className="count-badge">{items.length}</span>
      </div>
      <div className="review-list">
        {items.length ? items.map((item) => (
          <div className="review-item" key={item.question_id}>
            <strong>{item.topic} · {item.skill}</strong>
            <span>{item.text}</span>
          </div>
        )) : (
          <p className="empty-state">No missed items waiting. Keep practicing to strengthen retention.</p>
        )}
      </div>
    </article>
  );
}
