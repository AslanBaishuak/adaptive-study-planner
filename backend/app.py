"""
app.py
------
Small Flask API around the AdaptiveEngine. Run with:

    pip install flask flask-cors
    python app.py

Then open frontend/index.html (it calls this API at http://localhost:5000).
"""

import json
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from adaptive_engine import AdaptiveEngine

app = Flask(__name__)
CORS(app)  # allow the static frontend (opened as a file) to call this API

QUESTIONS_PATH = Path(__file__).parent / "questions.json"
with open(QUESTIONS_PATH, encoding="utf-8") as f:
    QUESTIONS = json.load(f)

engine = AdaptiveEngine(QUESTIONS)


@app.get("/api/next")
def next_question():
    user_id = request.args.get("user", "guest")
    topic = request.args.get("topic")  # optional filter: "math" | "vocab"
    question = engine.next_question(user_id, topic)
    if question is None:
        return jsonify({"done": True})
    # never send the answer index to the client before they've answered
    safe = {k: v for k, v in question.items() if k != "answer_index"}
    return jsonify({"done": False, "question": safe})


@app.post("/api/answer")
def submit_answer():
    body = request.get_json(force=True)
    user_id = body.get("user", "guest")
    question_id = body["question_id"]
    choice_index = body["choice_index"]
    result = engine.submit_answer(user_id, question_id, choice_index)
    return jsonify(result)


@app.get("/api/progress")
def progress():
    user_id = request.args.get("user", "guest")
    return jsonify(engine.progress(user_id))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
