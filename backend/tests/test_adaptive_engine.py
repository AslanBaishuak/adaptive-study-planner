import json
from pathlib import Path
import sys
import tempfile
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from adaptive_engine import AdaptiveEngine, DEFAULT_RATING, update_ratings


class RatingTests(unittest.TestCase):
    def test_correct_answer_raises_learner_rating(self):
        learner, question = update_ratings(1200, 1200, True)
        self.assertGreater(learner, 1200)
        self.assertLess(question, 1200)

    def test_incorrect_answer_lowers_learner_rating(self):
        learner, question = update_ratings(1200, 1200, False)
        self.assertLess(learner, 1200)
        self.assertGreater(question, 1200)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_directory.name) / "state.json"
        self.questions = json.loads((BACKEND_DIR / "questions.json").read_text(encoding="utf-8"))
        self.engine = AdaptiveEngine(self.questions, data_path=self.state_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_answer_is_persisted_and_restored(self):
        question = self.engine.next_question("learner", "math")
        self.engine.submit_answer("learner", question["id"], question["answer_index"])
        restored = AdaptiveEngine(self.questions, data_path=self.state_path)
        progress = restored.progress("learner")
        self.assertEqual(progress["questions_answered"], 1)
        self.assertEqual(progress["accuracy"], 100)
        self.assertGreater(progress["rating"], DEFAULT_RATING)

    def test_wrong_answer_enters_review_queue(self):
        question = self.engine.next_question("learner", "science")
        wrong_choice = (question["answer_index"] + 1) % len(question["choices"])
        self.engine.submit_answer("learner", question["id"], wrong_choice)
        queue = self.engine.review_queue("learner")
        self.assertEqual(queue[0]["question_id"], question["id"])

    def test_plan_is_local_and_has_requested_length(self):
        plan = self.engine.study_plan("learner", days=7, minutes_per_day=20)
        self.assertTrue(plan["generated_locally"])
        self.assertEqual(len(plan["sessions"]), 7)
        self.assertTrue(all(day["minutes"] == 20 for day in plan["sessions"]))

    def test_question_cycle_restarts_after_topic_is_completed(self):
        math_questions = [q for q in self.questions if q["topic"] == "math"]
        for question in math_questions:
            self.engine.submit_answer("learner", question["id"], question["answer_index"])
        next_question = self.engine.next_question("learner", "math")
        self.assertIsNotNone(next_question)
        self.assertEqual(next_question["topic"], "math")


if __name__ == "__main__":
    unittest.main()
