function MetricCard({ label, value, caption, accent = false }) {
  return (
    <article className={`metric-card ${accent ? "accent-card" : ""}`}>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      <span className="metric-caption">{caption}</span>
    </article>
  );
}

export default function Metrics({ progress }) {
  const answered = progress?.questions_answered ?? 0;
  return (
    <section className="metrics" aria-label="Learning statistics">
      <MetricCard
        label="Overall rating"
        value={progress?.rating ?? 1200}
        caption={answered ? `Best streak: ${progress.best_streak}` : "Starting level"}
        accent
      />
      <MetricCard label="Accuracy" value={`${progress?.accuracy ?? 0}%`} caption="Across all attempts" />
      <MetricCard label="Current streak" value={progress?.current_streak ?? 0} caption="Correct answers" />
      <MetricCard label="Questions answered" value={answered} caption="Saved locally" />
    </section>
  );
}
