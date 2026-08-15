import { useEffect, useState } from "react";
import { api } from "./api";
import FocusCard from "./components/FocusCard";
import Header from "./components/Header";
import MasteryGrid from "./components/MasteryGrid";
import Metrics from "./components/Metrics";
import PracticeSession from "./components/PracticeSession";
import ReviewQueue from "./components/ReviewQueue";
import StudyPlan from "./components/StudyPlan";

const USER_ID = "guest";

export default function App() {
  const [health, setHealth] = useState(null);
  const [topics, setTopics] = useState([]);
  const [progress, setProgress] = useState(null);
  const [plan, setPlan] = useState(null);
  const [question, setQuestion] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [days, setDays] = useState(7);
  const [minutes, setMinutes] = useState(20);
  const [questionLoading, setQuestionLoading] = useState(true);
  const [planLoading, setPlanLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const [healthData, topicsData, progressData, planData, questionData] = await Promise.all([
          api.health(),
          api.topics(),
          api.progress(USER_ID),
          api.studyPlan(USER_ID, 7, 20),
          api.nextQuestion(USER_ID),
        ]);
        if (!active) return;
        setHealth(healthData);
        setTopics(topicsData.topics);
        setProgress(progressData);
        setPlan(planData);
        setQuestion(questionData.question);
      } catch (requestError) {
        if (active) setError(`${requestError.message}. Start the Flask backend and reload.`);
      } finally {
        if (active) {
          setQuestionLoading(false);
          setPlanLoading(false);
        }
      }
    }
    initialize();
    return () => { active = false; };
  }, []);

  async function loadQuestion(topic = selectedTopic) {
    setQuestionLoading(true);
    setError("");
    try {
      const data = await api.nextQuestion(USER_ID, topic);
      setQuestion(data.question);
    } catch (requestError) {
      setQuestion(null);
      setError(requestError.message);
    } finally {
      setQuestionLoading(false);
    }
  }

  async function loadPlan(nextDays = days, nextMinutes = minutes) {
    setPlanLoading(true);
    try {
      setPlan(await api.studyPlan(USER_ID, nextDays, nextMinutes));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPlanLoading(false);
    }
  }

  async function refreshLearningData() {
    const [progressData, planData] = await Promise.all([
      api.progress(USER_ID),
      api.studyPlan(USER_ID, days, minutes),
    ]);
    setProgress(progressData);
    setPlan(planData);
  }

  async function changeTopic(topic) {
    setSelectedTopic(topic);
    await loadQuestion(topic);
  }

  async function changeDays(value) {
    setDays(value);
    await loadPlan(value, minutes);
  }

  async function changeMinutes(value) {
    setMinutes(value);
    await loadPlan(days, value);
  }

  async function resetProgress() {
    if (!window.confirm("Reset all saved progress for this local learner?")) return;
    try {
      await api.reset(USER_ID);
      const [progressData, planData, questionData] = await Promise.all([
        api.progress(USER_ID),
        api.studyPlan(USER_ID, days, minutes),
        api.nextQuestion(USER_ID, selectedTopic),
      ]);
      setProgress(progressData);
      setPlan(planData);
      setQuestion(questionData.question);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <main className="app-shell">
      <Header health={health} />
      {error && <div className="error-banner" role="alert">{error}</div>}
      <Metrics progress={progress} />

      <section className="dashboard-grid">
        <FocusCard plan={plan} userId={USER_ID} aiEnabled={health?.ai_enabled} />
        <ReviewQueue items={progress?.review_queue} />
      </section>

      <MasteryGrid items={progress?.topic_mastery} />

      <section className="workspace-grid">
        <PracticeSession
          userId={USER_ID}
          question={question}
          questionLoading={questionLoading}
          topics={topics}
          selectedTopic={selectedTopic}
          onTopicChange={changeTopic}
          onNext={() => loadQuestion()}
          onAnswered={refreshLearningData}
          aiEnabled={health?.ai_enabled}
        />
        <StudyPlan
          plan={plan}
          days={days}
          minutes={minutes}
          onDaysChange={changeDays}
          onMinutesChange={changeMinutes}
          onRefresh={() => loadPlan()}
          loading={planLoading}
        />
      </section>

      <footer>
        <p>Learning data stays in a local JSON file. Groq is called only when you press an AI button.</p>
        <button className="danger-link" type="button" onClick={resetProgress}>Reset learner progress</button>
      </footer>
    </main>
  );
}
