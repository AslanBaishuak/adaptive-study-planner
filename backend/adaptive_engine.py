"""
adaptive_engine.py
-------------------
A small, dependency-free implementation of Elo-style adaptive difficulty
selection for a quiz / exam-prep engine.

The core idea (borrowed from chess rating systems, and from how adaptive
testing engines like the GRE/CAT work under the hood): both the learner and
each question have a "rating". After every answer, both ratings update based
on whether the outcome was expected or a surprise. Over time this converges
the learner toward questions that sit right at their current skill edge —
hard enough to be useful, easy enough to be solvable.
"""

from dataclasses import dataclass, field
from typing import Optional
import math


K_FACTOR = 32          # how aggressively ratings move after one answer
DEFAULT_RATING = 1200  # starting rating for a new learner or question


def expected_score(a_rating: float, b_rating: float) -> float:
    """Standard Elo expected-score formula: probability A 'beats' B."""
    return 1.0 / (1.0 + math.pow(10, (b_rating - a_rating) / 400.0))


def update_ratings(learner_rating: float, question_rating: float, correct: bool,
                    k: float = K_FACTOR) -> tuple[float, float]:
    """
    Update both the learner's rating and the question's difficulty rating
    after one answer, the same way two Elo-rated players update after a game.

    - correct=True  -> learner "won" against the question
    - correct=False -> learner "lost" against the question
    """
    actual = 1.0 if correct else 0.0
    expected = expected_score(learner_rating, question_rating)

    new_learner = learner_rating + k * (actual - expected)
    # The question's rating moves the opposite direction, and more slowly —
    # a single answer shouldn't wildly swing an item's calibrated difficulty.
    new_question = question_rating + (k / 2) * ((1 - actual) - (1 - expected))

    return round(new_learner, 1), round(new_question, 1)


@dataclass
class LearnerState:
    user_id: str
    rating: float = DEFAULT_RATING
    answered_ids: set = field(default_factory=set)
    history: list = field(default_factory=list)  # list of {question_id, correct, rating_after}


class AdaptiveEngine:
    """In-memory adaptive engine. Swap the dict stores for a real DB in production."""

    def __init__(self, questions: list[dict]):
        # questions: list of {id, topic, text, choices, answer_index, difficulty}
        self.questions = {q["id"]: dict(q) for q in questions}
        self.learners: dict[str, LearnerState] = {}

    def _get_learner(self, user_id: str) -> LearnerState:
        if user_id not in self.learners:
            self.learners[user_id] = LearnerState(user_id=user_id)
        return self.learners[user_id]

    def next_question(self, user_id: str, topic: Optional[str] = None) -> Optional[dict]:
        """Pick the unanswered question whose difficulty is closest to the learner's rating."""
        learner = self._get_learner(user_id)
        candidates = [
            q for q in self.questions.values()
            if q["id"] not in learner.answered_ids and (topic is None or q["topic"] == topic)
        ]
        if not candidates:
            return None
        best = min(candidates, key=lambda q: abs(q["difficulty"] - learner.rating))
        return best

    def submit_answer(self, user_id: str, question_id: str, choice_index: int) -> dict:
        learner = self._get_learner(user_id)
        question = self.questions[question_id]
        correct = choice_index == question["answer_index"]

        new_learner_rating, new_question_rating = update_ratings(
            learner.rating, question["difficulty"], correct
        )

        learner.rating = new_learner_rating
        question["difficulty"] = new_question_rating
        learner.answered_ids.add(question_id)
        learner.history.append({
            "question_id": question_id,
            "correct": correct,
            "rating_after": new_learner_rating,
        })

        return {
            "correct": correct,
            "correct_answer_index": question["answer_index"],
            "new_rating": new_learner_rating,
            "questions_answered": len(learner.answered_ids),
        }

    def progress(self, user_id: str) -> dict:
        learner = self._get_learner(user_id)
        return {
            "user_id": user_id,
            "rating": learner.rating,
            "questions_answered": len(learner.answered_ids),
            "history": learner.history,
        }
