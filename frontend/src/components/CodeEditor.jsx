import { useState } from "react";
import { submitSolution, gradeExplanation } from "../api";

export default function CodeEditor({ question, onResult }) {
  const [code, setCode] = useState(question.starter_code || question.buggy_code || "");
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [grade, setGrade] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function run() {
    setBusy(true); setErr("");
    try {
      const res = await submitSolution({questionId: question.id, sourceCode: code, language: question.language || "python"});
      setResult(res); onResult(question.id, res);
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  }
  async function explain() {
    setBusy(true); setErr("");
    try { const res = await gradeExplanation(question.id, explanation); setGrade(res); onResult(question.id, {...result, explanation: res}); }
    catch (e) { setErr(e.message); } finally { setBusy(false); }
  }

  return <div className="assessment-card">
    <div className="editor-title"><span>YOUR CODE</span><span className="lang-chip">{question.language}</span></div>
    <textarea className="code-editor" value={code} onChange={e=>setCode(e.target.value)} spellCheck="false" />
    <div className="action-row"><button className="primary-btn small" onClick={run} disabled={busy}>{busy ? "Running…" : "Run & verify"}</button>{err && <span className="error-text">{err}</span>}</div>
    {result && <Result result={result} />}
    {result?.all_passed && <div className="explain-box">
      <div className="editor-title"><span>PROVE YOU UNDERSTAND IT</span><span className="ai-chip">AI GRADED</span></div>
      <textarea className="review-input" placeholder="Why does your solution work? Mention complexity and one edge case." value={explanation} onChange={e=>setExplanation(e.target.value)} />
      <button className="secondary-btn" onClick={explain} disabled={busy || !explanation.trim()}>Grade my reasoning</button>
      {grade && <GradeCard grade={grade} />}
    </div>}
  </div>;
}
function Result({result}) {
  return <div className={`result-box ${result.all_passed ? "pass" : "fail"}`}>
    <strong>{result.all_passed ? "🎉 All hidden checks passed" : `${result.passed}/${result.total} checks passed`}</strong>
    <div className="case-list">{(result.details||[]).map((d,i)=><div className="case-row" key={i}><span>{d.passed?"✓":"×"}</span><code>{d.input}</code><em>{d.passed?"passed":d.stderr||"output mismatch"}</em></div>)}</div>
  </div>;
}
export function GradeCard({grade}) {
  return <div className="grade-card"><div className="grade-score">{grade.score}<small>/100</small></div><div><b>Reasoning check</b><p>{grade.feedback}</p></div></div>;
}
