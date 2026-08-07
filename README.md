# Adaptive Study Planner

A personalized quiz engine that adjusts question difficulty in real time
based on performance — the same core idea behind adaptive exam-prep
systems, implemented from scratch with a small Elo-rating algorithm.

## Why I built this

At my internship at Outpeer AI I help build and curate datasets that feed
into an AI system for personalized entrance-exam prep. I wanted to
understand — and build myself — the piece that actually *uses* that kind
of data: an engine that tracks a learner's skill level and serves them
questions right at the edge of what they can do, instead of a static quiz.

## How it works

Both the learner and every question have a numeric rating (starting at
1200, same convention as chess Elo). After each answer:

- If the learner answers correctly, their rating moves up — more if the
  question was hard relative to their rating, less if it was easy (an easy
  win barely moves the needle).
- If they answer incorrectly, their rating moves down, and the question's
  own difficulty rating adjusts slightly too — so mis-calibrated questions
  self-correct over time.
- The next question served is always the closest match to the learner's
  *current* rating, so difficulty tracks skill automatically.

The rating math lives entirely in [`backend/adaptive_engine.py`](backend/adaptive_engine.py)
and is unit-testable independent of the API or UI.

## Project structure

```
adaptive-study-planner/
├── backend/
│   ├── app.py              # Flask API (3 endpoints: next, answer, progress)
│   ├── adaptive_engine.py  # Elo-based adaptive difficulty logic
│   ├── questions.json      # Sample question bank (math + vocab)
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js            # Talks to the API with fetch()
```

## Run it locally

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python app.py          # runs at http://localhost:5000

# 2. Frontend (in a second terminal / just open the file)
cd ../frontend
open index.html        # or double-click it
```

The frontend is a static page that calls the local API — no build step.

## Possible extensions

- Swap the in-memory stores in `AdaptiveEngine` for a real database
- Add real user accounts instead of a single "guest" user
- Chart rating-over-time using the `/api/progress` history
- Expand the question bank and add per-topic ratings instead of one global rating
