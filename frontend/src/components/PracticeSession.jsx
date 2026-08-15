import { useEffect, useState } from "react";
import { api } from "../api";

export default function PracticeSession({
  userId,
  question,
  questionLoading,
  topics,
  selectedTopic,
  onTopicChange,
  onNext,
  onAnswered,
  aiEnabled,
}) {
  const [selectedChoice, setSelectedChoice] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    setSelectedChoice(null);
    setResult(null);
    setError("");
    setAiExplanation("");
  }, [question?.id]);

  async function submitAnswer(choiceIndex) {
    if (!question || submitting || result) return;
    setSelectedChoice(choiceIndex);
    setSubmitting(true);
    setError("");
    try {
      const data = await api.submitAnswer({
        user: userId,
        question_id: question.id,
        choice_index: choiceIndex,
      });
      setResult(data);
      await onAnswered();
    } catch (requestError) {
      setSelectedChoice(null);
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function askForExplanation() {
    setAiLoading(true);
    setAiExplanation("Generating one deeper explanation…");
    try {
      const data = await api.explain(question.id, selectedChoice);
      setAiExplanation(data.explanation);
    } catch (requestError) {
      setAiExplanation(requestError.message);
    } finally {
      setAiLoading(false);
    }
  }

  function choiceClass(index) {
    if (!result) return "choice-button";
    if (index === result.correct_answer_index) return "choice-button correct";
    if (index === selectedChoice && !result.correct) return "choice-button wrong";
    return "choice-button";
  }

  const ratingChange = result
    ? `${result.rating_change >= 0 ? "+" : ""}${result.rating_change}`
    : "";

  return (
    <article className="panel practice-panel">
      <div className="section-heading practice-heading">
        <div>
          <p className="eyebrow">Adaptive practice</p>
          <h2>Question at your level</h2>
        </div>
        <label className="select-control">
          <span>Topic</span>
          <select value={selectedTopic} onChange={(event) => onTopicChange(event.target.value)}>
            <option value="">Smart mix</option>
            {topics.map((topic) => (
              <option value={topic.id} key={topic.id}>
                {topic.id} ({topic.question_count})
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="question-card" aria-live="polite">
        {questionLoading ? (
          <p className="loading">Selecting a question near your current level…</p>
        ) : question ? (
          <>
            <div className="question-meta">
              <span>{question.topic}</span>
              <span>{question.skill}</span>
              <span>difficulty {Math.round(question.difficulty)}</span>
            </div>
            <p className="question-text">{question.text}</p>
            <div className="choices">
              {question.choices.map((choice, index) => (
                <button
                  className={choiceClass(index)}
                  type="button"
                  key={`${question.id}-${index}`}
                  disabled={submitting || Boolean(result)}
                  onClick={() => submitAnswer(index)}
                >
                  {choice}
                </button>
              ))}
            </div>
          </>
        ) : (
          <p className="loading">No question is available.</p>
        )}
      </div>

      <p className="feedback" aria-live="polite">
        {error || (result && (result.correct
          ? `Correct. Rating ${ratingChange}; ${result.topic_mastery.topic} mastery is now ${result.topic_mastery.mastery}%.`
          : `Not quite. Rating ${ratingChange}; this question was added to your review queue.`))}
      </p>

      {result && (
        <div className="explanation-box">
          <div>
            <span className="explanation-label">Why this answer works</span>
            <p>{result.explanation}</p>
          </div>
          {aiEnabled && (
            <button className="secondary-button" type="button" onClick={askForExplanation} disabled={aiLoading}>
              {aiLoading ? "Asking AI…" : "Ask AI for a deeper explanation"}
            </button>
          )}
          {aiExplanation && <div className="ai-detail" aria-live="polite">{aiExplanation}</div>}
        </div>
      )}

      {result && (
        <button className="primary-button full-width" type="button" onClick={onNext}>
          Continue to next question
        </button>
      )}
    </article>
  );
}
