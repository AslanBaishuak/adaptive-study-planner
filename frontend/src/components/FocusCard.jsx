import { useState } from "react";
import { api } from "../api";

export default function FocusCard({ plan, userId, aiEnabled }) {
  const [coaching, setCoaching] = useState("");
  const [loading, setLoading] = useState(false);

  async function askCoach() {
    setLoading(true);
    setCoaching("Generating three recommendations from your current progress…");
    try {
      const data = await api.coach(userId);
      setCoaching(data.coaching);
    } catch (error) {
      setCoaching(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="panel focus-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Recommended next step</p>
          <h2>{plan?.primary_focus ? `Focus on ${plan.primary_focus}` : "Complete a short diagnostic"}</h2>
        </div>
        {aiEnabled && (
          <button className="text-button" type="button" onClick={askCoach} disabled={loading}>
            {loading ? "Asking coach…" : "Ask optional AI coach"}
          </button>
        )}
      </div>
      <p className="focus-reason">
        {plan?.reason || "Answer a few mixed questions so the planner can identify your strongest and weakest topics."}
      </p>
      {coaching && <div className="coach-output" aria-live="polite">{coaching}</div>}
    </article>
  );
}
