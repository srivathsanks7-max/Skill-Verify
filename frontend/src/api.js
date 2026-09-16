const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error("The server is unreachable. If you are running locally, start the Flask app.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed: ${res.status}`);
  return data;
}

export function loginWithGithub() {
  window.location.href = `${API_BASE}/auth/github/login`;
}
export const getCurrentUser = () => request("/auth/me");
export const logout = () => request("/auth/logout", { method: "POST" });

export function startTest(payload) {
  return request("/api/start-test", { method: "POST", body: JSON.stringify(payload) });
}
export function submitSolution(payload) {
  return request("/api/submit", { method: "POST", body: JSON.stringify({
    question_id: payload.questionId,
    source_code: payload.sourceCode,
    language: payload.language || "python",
  })});
}
export function gradeExplanation(questionId, explanation) {
  return request("/api/explanation", { method: "POST", body: JSON.stringify({
    question_id: questionId, explanation
  })});
}
export function gradeReview(questionId, review) {
  return request("/api/review", { method: "POST", body: JSON.stringify({
    question_id: questionId, review
  })});
}
export const getScore = () => request("/api/score");
export const createCredential = () => request("/api/credential", { method: "POST" });
export function matchJob(jobDescription) {
  return request("/api/job-match", { method: "POST", body: JSON.stringify({ job_description: jobDescription })});
}
export const getCareerPlan = () => request("/api/career-plan");
