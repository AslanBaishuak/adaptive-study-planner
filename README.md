# Adaptive Study Planner

A local-first learning app that turns quiz performance into a real adaptive study plan. It selects questions near the learner's current skill level, tracks per-topic mastery, queues missed questions for review, persists progress, and builds a personalized seven-day schedule.

The complete planner works without an AI API. Groq is optional and is called only when the learner deliberately asks for deeper tutoring or coaching.

## What makes it adaptive

- **Elo-based difficulty matching:** learner and question ratings update after every answer.
- **Per-topic skill ratings:** math, vocabulary, science, and programming adapt independently.
- **Evidence-based mastery:** difficulty, accuracy, and number of attempts contribute to each topic's mastery score.
- **Weak-topic prioritization:** smart-mix practice and the weekly plan favor topics with the lowest demonstrated mastery.
- **Spaced review queue:** the latest missed questions remain visible for targeted review.
- **Persistent progress:** learner history survives backend restarts in a local JSON file.
- **Adaptive schedule:** users can generate 5–14 day plans for 10–90 minutes per day without using AI tokens.
- **Optional AI tutor:** one bounded Groq call happens only when the learner presses an AI button.

## Zero-cost architecture

| Feature | Implementation | AI tokens |
|---|---|---:|
| Question selection | Local Python Elo engine | 0 |
| Answer checking | Local question bank | 0 |
| Explanations | Curated local explanations | 0 |
| Topic mastery | Local deterministic calculation | 0 |
| Review queue | Local learner history | 0 |
| Weekly study plan | Local deterministic planner | 0 |
| Deeper explanation | Optional Groq button | One request |
| AI coaching | Optional Groq button | One request |

There are no automatic AI calls, background retries, or paid services required by the core application.

## Project structure

```text
adaptive-study-planner/
├── .env.example
├── .gitignore
├── backend/
│   ├── app.py
│   ├── adaptive_engine.py
│   ├── questions.json
│   ├── requirements.txt
│   └── tests/
│       └── test_adaptive_engine.py
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx
        ├── api.js
        ├── main.jsx
        ├── styles.css
        └── components/
```

Runtime learner data is created at `backend/data/learner_state.json` and is ignored by Git.

## Run locally on Windows

From the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
```

Start the backend in the first terminal:

```powershell
cd backend
python app.py
```

Start the React frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to the Flask backend at `http://localhost:5000`, so no additional configuration is needed for local development.

## Enable optional Groq tutoring

The adaptive planner does not need Groq. To enable the two optional AI buttons, create a free Groq key and set it only in the current terminal:

```powershell
$env:GROQ_API_KEY="your-new-key"
$env:GROQ_MODEL="llama-3.1-8b-instant"
python app.py
```

Never paste a real API key into `app.py`, frontend code, `.env.example`, README files, Git commits, or screenshots.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend and optional-AI status |
| GET | `/api/topics` | Available topics and question counts |
| GET | `/api/next` | Select the next adaptive question |
| POST | `/api/answer` | Check an answer and update ratings |
| GET | `/api/progress` | Mastery, accuracy, streaks, and review queue |
| GET | `/api/study-plan` | Generate a local adaptive schedule |
| GET | `/api/recommendation` | Get a local zero-token recommendation |
| POST | `/api/explain` | Request one optional Groq explanation |
| POST | `/api/coach` | Request one optional Groq coaching response |
| POST | `/api/reset` | Reset one learner's local progress |

## Run tests

Backend validation:

```powershell
cd backend
python -m unittest discover -s tests -v
python -m py_compile app.py adaptive_engine.py
```

Frontend validation:

```powershell
cd frontend
npm install
npm run build
```

The automated suite covers rating direction, persistence, review queues, plan generation, and practice-cycle behavior. The Vite build verifies the React component tree and production bundle.

## Current limitations

- The demo uses a local learner ID rather than full authentication.
- JSON persistence is designed for a local portfolio demo, not concurrent production traffic.
- The built-in question bank is intentionally compact. A production version should use a database and a larger reviewed item bank.
- AI output can be wrong; curated local explanations remain the default source of truth.
