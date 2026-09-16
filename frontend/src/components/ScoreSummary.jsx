import { createCredential } from "../api";
import { useState } from "react";

export default function ScoreSummary({score,onRestart}) {
  const [credential,setCredential]=useState(null), [busy,setBusy]=useState(false);
  async function share() { setBusy(true); try { const c=await createCredential(); setCredential(c); } finally { setBusy(false); } }
  const pct=score.score_percent||0;
  return <section className="score-page">
    <div className="score-hero">
      <div className="score-circle"><strong>{pct}</strong><span>/100</span></div>
      <div><div className="section-kicker">ASSESSMENT COMPLETE</div><h1>Your verification snapshot</h1><p>Evidence, execution and reasoning combined into one assessment record.</p></div>
    </div>
    <div className="stats-grid">
      <div><b>{score.questions_fully_passed}</b><span>fully verified</span></div>
      <div><b>{score.passed_test_cases}/{score.total_test_cases}</b><span>test cases</span></div>
      <div><b>{score.attempted_questions}/{score.total_questions}</b><span>attempted</span></div>
    </div>
    <div className="credential-card">
      <div><span className="ai-chip">SIGNED CREDENTIAL</span><h3>Carry your proof with you.</h3><p>Generate a public verification page with your verified skills and issue date.</p>
      <button className="primary-btn small" onClick={share} disabled={busy}>{busy?"Creating…":"Create shareable credential"}</button>
      {credential && <div className="credential-link"><code>{`${window.location.origin}/verify/${credential.id}`}</code><a href={`/verify/${credential.id}`} target="_blank" rel="noreferrer">Open ↗</a></div>}</div>
    </div>
    <button className="secondary-btn" onClick={onRestart}>Start another verification</button>
  </section>;
}
