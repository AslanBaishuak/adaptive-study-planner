const API_BASE = import.meta.env.VITE_API_BASE || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}

const jsonOptions = (method, body) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  health: () => request("/health"),
  topics: () => request("/topics"),
  nextQuestion: (user, topic = "") =>
    request(`/next?user=${encodeURIComponent(user)}${topic ? `&topic=${encodeURIComponent(topic)}` : ""}`),
  submitAnswer: (payload) => request("/answer", jsonOptions("POST", payload)),
  progress: (user) => request(`/progress?user=${encodeURIComponent(user)}`),
  studyPlan: (user, days, minutes) =>
    request(`/study-plan?user=${encodeURIComponent(user)}&days=${days}&minutes=${minutes}`),
  explain: (questionId, choiceIndex) =>
    request("/explain", jsonOptions("POST", { question_id: questionId, choice_index: choiceIndex })),
  coach: (user) => request(`/coach?user=${encodeURIComponent(user)}`, { method: "POST" }),
  reset: (user) => request("/reset", jsonOptions("POST", { user })),
};
