"""Adaptive learning engine used by the Flask API.

The engine deliberately keeps the important learning logic local: Elo-style
question selection, per-topic mastery, weak-topic detection, review queues,
streaks, progress summaries, and seven-day study plans do not require an AI
provider or consume tokens.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Optional


K_FACTOR = 32
DEFAULT_RATING = 1200.0
MIN_RATING = 600.0
MAX_RATING = 1800.0


def expected_score(learner_rating: float, question_rating: float) -> float:
    """Return the probability that the learner answers correctly."""
    return 1.0 / (1.0 + math.pow(10, (question_rating - learner_rating) / 400.0))


def update_ratings(
    learner_rating: float,
    question_rating: float,
    correct: bool,
    k: float = K_FACTOR,
) -> tuple[float, float]:
    """Update learner skill and estimated question difficulty."""
    actual = 1.0 if correct else 0.0
    expected = expected_score(learner_rating, question_rating)
    new_learner = learner_rating + k * (actual - expected)
    new_question = question_rating + (k / 2) * (expected - actual)
    return (
        round(min(MAX_RATING, max(MIN_RATING, new_learner)), 1),
        round(min(MAX_RATING, max(MIN_RATING, new_question)), 1),
    )


@dataclass
class LearnerState:
    user_id: str
    rating: float = DEFAULT_RATING
    topic_ratings: dict[str, float] = field(default_factory=dict)
    answered_ids: set[str] = field(default_factory=set)
    history: list[dict] = field(default_factory=list)
    current_streak: int = 0
    best_streak: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["answered_ids"] = sorted(self.answered_ids)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LearnerState":
        return cls(
            user_id=str(data["user_id"]),
            rating=float(data.get("rating", DEFAULT_RATING)),
            topic_ratings={
                str(topic): float(rating)
                for topic, rating in data.get("topic_ratings", {}).items()
            },
            answered_ids=set(data.get("answered_ids", [])),
            history=list(data.get("history", [])),
            current_streak=int(data.get("current_streak", 0)),
            best_streak=int(data.get("best_streak", 0)),
        )


class AdaptiveEngine:
    """Persistent, dependency-free adaptive learning engine."""

    def __init__(self, questions: list[dict], data_path: Optional[Path] = None):
        self.questions = {q["id"]: dict(q) for q in questions}
        self.data_path = Path(data_path) if data_path else None
        self.learners: dict[str, LearnerState] = {}
        self._load()

    @property
    def topics(self) -> list[str]:
        return sorted({q["topic"] for q in self.questions.values()})

    def _load(self) -> None:
        if not self.data_path or not self.data_path.exists():
            return
        try:
            payload = json.loads(self.data_path.read_text(encoding="utf-8"))
            for user_id, data in payload.get("learners", {}).items():
                self.learners[user_id] = LearnerState.from_dict(data)
            for question_id, rating in payload.get("question_ratings", {}).items():
                if question_id in self.questions:
                    self.questions[question_id]["difficulty"] = float(rating)
        except (OSError, ValueError, TypeError, KeyError):
            # A damaged local state file should never prevent the app from starting.
            self.learners = {}

    def _save(self) -> None:
        if not self.data_path:
            return
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "learners": {
                user_id: learner.to_dict()
                for user_id, learner in self.learners.items()
            },
            "question_ratings": {
                question_id: question["difficulty"]
                for question_id, question in self.questions.items()
            },
        }
        temporary_path = self.data_path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary_path.replace(self.data_path)

    def _get_learner(self, user_id: str) -> LearnerState:
        if user_id not in self.learners:
            self.learners[user_id] = LearnerState(
                user_id=user_id,
                topic_ratings={topic: DEFAULT_RATING for topic in self.topics},
            )
        learner = self.learners[user_id]
        for topic in self.topics:
            learner.topic_ratings.setdefault(topic, DEFAULT_RATING)
        return learner

    def _history_for_topic(self, learner: LearnerState, topic: str) -> list[dict]:
        return [entry for entry in learner.history if entry.get("topic") == topic]

    def _topic_summary(self, learner: LearnerState, topic: str) -> dict:
        history = self._history_for_topic(learner, topic)
        attempts = len(history)
        correct = sum(1 for entry in history if entry.get("correct"))
        accuracy = round((correct / attempts) * 100) if attempts else 0
        rating = round(learner.topic_ratings.get(topic, DEFAULT_RATING))
        rating_score = max(0.0, min(100.0, ((rating - 800) / 800) * 100))
        confidence = min(1.0, attempts / 8)
        mastery = round((0.65 * rating_score + 0.35 * accuracy) * confidence)

        if attempts == 0:
            status = "Not started"
        elif mastery < 35:
            status = "Needs focus"
        elif mastery < 60:
            status = "Developing"
        elif mastery < 80:
            status = "Proficient"
        else:
            status = "Mastered"

        return {
            "topic": topic,
            "rating": rating,
            "attempts": attempts,
            "correct": correct,
            "accuracy": accuracy,
            "mastery": mastery,
            "status": status,
        }

    def next_question(self, user_id: str, topic: Optional[str] = None) -> Optional[dict]:
        learner = self._get_learner(user_id)
        if topic and topic not in self.topics:
            return None

        candidates = [
            question
            for question in self.questions.values()
            if question["id"] not in learner.answered_ids
            and (topic is None or question["topic"] == topic)
        ]

        # Start a fresh practice cycle once every matching question was attempted.
        if not candidates:
            completed_ids = {
                question["id"]
                for question in self.questions.values()
                if topic is None or question["topic"] == topic
            }
            learner.answered_ids.difference_update(completed_ids)
            candidates = [
                question
                for question in self.questions.values()
                if topic is None or question["topic"] == topic
            ]

        if not candidates:
            return None

        summaries = {name: self._topic_summary(learner, name) for name in self.topics}

        def priority(question: dict) -> float:
            question_topic = question["topic"]
            target = learner.topic_ratings.get(question_topic, learner.rating)
            distance = abs(float(question["difficulty"]) - target)
            topic_summary = summaries[question_topic]
            weakness_bonus = (100 - topic_summary["mastery"]) * 1.5
            return distance - weakness_bonus

        return min(candidates, key=priority)

    def submit_answer(self, user_id: str, question_id: str, choice_index: int) -> dict:
        if question_id not in self.questions:
            raise KeyError("Unknown question_id")

        question = self.questions[question_id]
        if not isinstance(choice_index, int) or not 0 <= choice_index < len(question["choices"]):
            raise ValueError("choice_index is out of range")

        learner = self._get_learner(user_id)
        correct = choice_index == question["answer_index"]
        previous_rating = learner.rating
        previous_topic_rating = learner.topic_ratings.get(question["topic"], DEFAULT_RATING)
        old_question_rating = float(question["difficulty"])

        learner.rating, question["difficulty"] = update_ratings(
            learner.rating, old_question_rating, correct
        )
        new_topic_rating, _ = update_ratings(
            previous_topic_rating, old_question_rating, correct, k=28
        )
        learner.topic_ratings[question["topic"]] = new_topic_rating
        learner.answered_ids.add(question_id)

        if correct:
            learner.current_streak += 1
            learner.best_streak = max(learner.best_streak, learner.current_streak)
        else:
            learner.current_streak = 0

        learner.history.append(
            {
                "question_id": question_id,
                "topic": question["topic"],
                "skill": question.get("skill", question["topic"]),
                "correct": correct,
                "choice_index": choice_index,
                "rating_before": previous_rating,
                "rating_after": learner.rating,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()

        return {
            "correct": correct,
            "correct_answer_index": question["answer_index"],
            "explanation": question.get("explanation", "Review the correct answer and try a similar problem."),
            "new_rating": learner.rating,
            "rating_change": round(learner.rating - previous_rating, 1),
            "topic_mastery": self._topic_summary(learner, question["topic"]),
            "questions_answered": len(learner.history),
            "current_streak": learner.current_streak,
        }

    def review_queue(self, user_id: str, limit: int = 5) -> list[dict]:
        learner = self._get_learner(user_id)
        latest_result: dict[str, dict] = {}
        for entry in learner.history:
            latest_result[entry["question_id"]] = entry

        queue = []
        for question_id, entry in reversed(list(latest_result.items())):
            if entry.get("correct"):
                continue
            question = self.questions.get(question_id)
            if not question:
                continue
            queue.append(
                {
                    "question_id": question_id,
                    "topic": question["topic"],
                    "skill": question.get("skill", question["topic"]),
                    "text": question["text"],
                }
            )
            if len(queue) >= limit:
                break
        return queue

    def progress(self, user_id: str) -> dict:
        learner = self._get_learner(user_id)
        topic_mastery = [self._topic_summary(learner, topic) for topic in self.topics]
        attempted = [item for item in topic_mastery if item["attempts"] > 0]
        weak_topics = sorted(
            attempted or topic_mastery,
            key=lambda item: (item["mastery"], item["accuracy"], item["rating"]),
        )[:2]
        correct_count = sum(1 for entry in learner.history if entry.get("correct"))
        total = len(learner.history)

        return {
            "user_id": user_id,
            "rating": round(learner.rating),
            "questions_answered": total,
            "correct_answers": correct_count,
            "accuracy": round((correct_count / total) * 100) if total else 0,
            "current_streak": learner.current_streak,
            "best_streak": learner.best_streak,
            "topic_mastery": topic_mastery,
            "weak_topics": [item["topic"] for item in weak_topics],
            "review_queue": self.review_queue(user_id),
            "recent_history": learner.history[-12:],
        }

    def study_plan(self, user_id: str, days: int = 7, minutes_per_day: int = 20) -> dict:
        learner = self._get_learner(user_id)
        summaries = [self._topic_summary(learner, topic) for topic in self.topics]
        ranked = sorted(
            summaries,
            key=lambda item: (item["mastery"], item["attempts"], item["rating"]),
        )
        focus_cycle = [item["topic"] for item in ranked]
        # Repeat a focus topic only after there is evidence that it is weak.
        if ranked and ranked[0]["attempts"] > 0:
            focus_cycle.insert(1, ranked[0]["topic"])

        sessions = []
        for day_index in range(days):
            topic = focus_cycle[day_index % len(focus_cycle)]
            summary = next(item for item in summaries if item["topic"] == topic)
            review_count = min(3, len(self.review_queue(user_id, limit=10)))
            tasks = [
                {"label": "Warm up", "detail": "Answer 2 questions near your current level", "minutes": 5},
                {
                    "label": "Focused practice",
                    "detail": f"Practice {topic} around difficulty {summary['rating']}",
                    "minutes": max(8, minutes_per_day - 10),
                },
                {
                    "label": "Review",
                    "detail": f"Retry {review_count or 2} missed or challenging questions",
                    "minutes": 5,
                },
            ]
            if day_index == days - 1:
                tasks[-1] = {
                    "label": "Weekly check",
                    "detail": "Complete a mixed-topic check and compare mastery scores",
                    "minutes": 5,
                }
            sessions.append(
                {
                    "day": day_index + 1,
                    "focus_topic": topic,
                    "goal": f"Move {topic} from {summary['status'].lower()} toward the next mastery level",
                    "minutes": minutes_per_day,
                    "tasks": tasks,
                }
            )

        has_evidence = any(item["attempts"] > 0 for item in summaries)
        primary_focus = ranked[0] if ranked and has_evidence else None
        if not primary_focus:
            reason = "Complete a few mixed questions so the plan can identify a focus area."
        elif primary_focus["attempts"] == 0:
            reason = (
                f"{primary_focus['topic'].title()} has not been assessed yet, "
                "so it is scheduled early to establish a baseline."
            )
        else:
            reason = (
                f"{primary_focus['topic'].title()} currently has the lowest demonstrated mastery score "
                f"({primary_focus['mastery']}%)."
            )

        return {
            "generated_locally": True,
            "days": days,
            "minutes_per_day": minutes_per_day,
            "primary_focus": primary_focus["topic"] if primary_focus else None,
            "reason": reason,
            "sessions": sessions,
        }

    def reset(self, user_id: str) -> None:
        self.learners.pop(user_id, None)
        self._save()
