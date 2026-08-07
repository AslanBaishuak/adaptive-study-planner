const API_BASE = "http://localhost:5000/api";
const USER_ID = "guest"; // swap for a real login in a fuller version

const ratingEl = document.getElementById("rating");
const answeredEl = document.getElementById("answered-count");
const cardEl = document.getElementById("question-card");
const feedbackEl = document.getElementById("feedback");
const topicSelect = document.getElementById("topic");

let currentQuestion = null;

async function loadNextQuestion() {
  feedbackEl.textContent = "";
  cardEl.innerHTML = `<p class="loading">Loading next question…</p>`;
  const topic = topicSelect.value;
  const url = `${API_BASE}/next?user=${encodeURIComponent(USER_ID)}${topic ? `&topic=${topic}` : ""}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.done) {
      cardEl.innerHTML = `<p>You've answered every question in this set — nice work.</p>`;
      return;
    }
    currentQuestion = data.question;
    renderQuestion(currentQuestion);
  } catch (err) {
    cardEl.innerHTML = `<p class="loading">Couldn't reach the API. Is <code>python app.py</code> running on port 5000?</p>`;
  }
}

function renderQuestion(q) {
  cardEl.innerHTML = `
    <span class="difficulty-badge">${q.topic} · difficulty ${Math.round(q.difficulty)}</span>
    <p class="question-text">${q.text}</p>
    <div id="choices"></div>
  `;
  const choicesEl = document.getElementById("choices");
  q.choices.forEach((choice, i) => {
    const btn = document.createElement("button");
    btn.className = "choice-btn";
    btn.textContent = choice;
    btn.addEventListener("click", () => submitAnswer(i));
    choicesEl.appendChild(btn);
  });
}

async function submitAnswer(choiceIndex) {
  const buttons = document.querySelectorAll(".choice-btn");
  buttons.forEach((b) => (b.disabled = true));

  const res = await fetch(`${API_BASE}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user: USER_ID,
      question_id: currentQuestion.id,
      choice_index: choiceIndex,
    }),
  });
  const result = await res.json();

  buttons[choiceIndex].classList.add(result.correct ? "correct" : "wrong");
  if (!result.correct) buttons[result.correct_answer_index].classList.add("correct");

  feedbackEl.textContent = result.correct
    ? "Correct! Rating updated."
    : "Not quite — rating updated so the next question calibrates better.";

  ratingEl.textContent = Math.round(result.new_rating);
  answeredEl.textContent = result.questions_answered;

  setTimeout(loadNextQuestion, 1400);
}

topicSelect.addEventListener("change", loadNextQuestion);

loadNextQuestion();
