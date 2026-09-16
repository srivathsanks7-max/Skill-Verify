import { useState } from "react";
import { gradeReview } from "../api";
import CodeEditor, { GradeCard } from "./CodeEditor";

export default function QuestionPanel({ question, onResult }) {
  const [review, setReview] = useState("");
  const [grade, setGrade] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!question) return null;
  const type = question.assessment_type;

  async function submitReview() {
    setBusy(true); setError("");
    try { const r = await gradeReview(question.id, review); setGrade(r); onResult(question.id, {review:r}); }
    catch(e) { setError(e.message); } finally { setBusy(false); }
  }

  return <article className="question-wrap">
    <div className="question-meta"><span>CHALLENGE {question.id.slice(0,6).toUpperCase()}</span><span className="difficulty">{question.difficulty}</span></div>
    <div className="question-heading"><h2>{question.title}</h2><span className={`type-badge ${type}`}>{type === "debug" ? "🐞 DEBUG" : type === "review" ? "🔎 REVIEW" : "⌘ CODE"}</span></div>
    <div className="target-skill">Target skill · <b>{question.skill_tested}</b></div>
    <p className="question-description">{question.description}</p>
    {question.test_case_inputs?.length > 0 && <details className="sample-box"><summary>View sample inputs</summary>{question.test_case_inputs.map((x,i)=><code key={i}>{x}</code>)}</details>}
    {type === "review" ? <div className="assessment-card">
      <div className="editor-title"><span>REVIEW THE SNIPPET</span><span className="lang-chip">{question.language}</span></div>
      <pre className="code-preview">{question.code}</pre>
      <textarea className="review-input tall" placeholder="List the issues you found, why they matter, and how you would fix them…" value={review} onChange={e=>setReview(e.target.value)} />
      <button className="primary-btn small" onClick={submitReview} disabled={busy || !review.trim()}>{busy ? "Grading…" : "Submit code review"}</button>
      {error && <p className="error-text">{error}</p>}{grade && <GradeCard grade={grade} />}
    </div> : <CodeEditor question={question} onResult={onResult} />}
  </article>;
}
