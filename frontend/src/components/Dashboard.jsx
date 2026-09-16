import { useState } from "react";
import { startTest, getScore, matchJob, getCareerPlan } from "../api";
import SkillProfile from "./SkillProfile";
import ModeSelect from "./ModeSelect";
import QuestionPanel from "./QuestionPanel";
import ScoreSummary from "./ScoreSummary";

export default function Dashboard({user,onLogout}) {
  const [tab,setTab]=useState("verify"), [stage,setStage]=useState("start");
  const [profile,setProfile]=useState(null), [questions,setQuestions]=useState([]), [active,setActive]=useState(0), [results,setResults]=useState({});
  const [score,setScore]=useState(null), [error,setError]=useState("");
  const [job,setJob]=useState(""), [jobResult,setJobResult]=useState(null), [plan,setPlan]=useState(null), [busy,setBusy]=useState(false);

  async function begin(payload) {
    setBusy(true); setError(""); setStage("loading");
    try { const r=await startTest(payload); setProfile(r.skill_profile); setQuestions(r.questions); setResults({}); setActive(0); setStage("test"); }
    catch(e){setError(e.message);setStage("start");} finally{setBusy(false);}
  }
  function handleResult(id,r){setResults(prev=>({...prev,[id]:r}));}
  async function finish(){try{setScore(await getScore());setStage("score")}catch(e){setError(e.message)}}
  function restart(){setStage("start");setQuestions([]);setScore(null);setResults({});}
  async function runJob(){setBusy(true);setError("");try{setJobResult(await matchJob(job));}catch(e){setError(e.message)}finally{setBusy(false)}}
  async function runPlan(){setBusy(true);try{setPlan(await getCareerPlan())}catch(e){setError(e.message)}finally{setBusy(false)}}

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand-row"><span className="brand-mark">SV</span><span>Skill<span>Verify</span></span></div>
      <nav className="topnav">{[["verify","Verify"],["job","Job match"],["plan","7-day plan"]].map(([id,label])=><button className={tab===id?"active":""} onClick={()=>setTab(id)} key={id}>{label}</button>)}</nav>
      <div className="user-area">{user.avatar_url&&<img src={user.avatar_url} />}{user.name||user.username}<button onClick={onLogout}>Log out</button></div>
    </header>
    {error&&<div className="global-error">{error}<button onClick={()=>setError("")}>×</button></div>}
    <div className="dashboard">
      <SkillProfile profile={profile}/>
      <main className="main-panel">
        {tab==="verify" && <>
          {stage==="start"&&<ModeSelect onStart={begin}/>}
          {stage==="loading"&&<Loading/>}
          {stage==="test"&&<section className="test-area">
            <div className="test-top"><div><div className="section-kicker">ADAPTIVE VERIFICATION</div><h1>Let's test the evidence.</h1></div><div className="attempt-pill">{Object.keys(results).length}/{questions.length} complete</div></div>
            <div className="question-tabs">{questions.map((q,i)=><button key={q.id} className={i===active?"active":""} onClick={()=>setActive(i)}>{i+1}<span>{q.assessment_type}</span>{results[q.id]?"✓":""}</button>)}</div>
            <QuestionPanel question={questions[active]} onResult={handleResult}/>
            <div className="finish-row"><span>Complete the challenges you want to include in your snapshot.</span><button className="primary-btn small" onClick={finish} disabled={!Object.keys(results).length}>View verification →</button></div>
          </section>}
          {stage==="score"&&score&&<ScoreSummary score={score} onRestart={restart}/>}
        </>}
        {tab==="job"&&<section className="tool-page"><div className="section-kicker">JOB MATCH</div><h1>Am I ready for <span>this role?</span></h1><p>Paste a job description and compare its technical requirements against repository evidence and your verified profile.</p><textarea className="job-box" placeholder="Paste the job description here…" value={job} onChange={e=>setJob(e.target.value)}/><button className="primary-btn" onClick={runJob} disabled={busy||!job.trim()}>{busy?"Analyzing…":"Analyze this role →"}</button>{jobResult&&<JobResult data={jobResult}/>}</section>}
        {tab==="plan"&&<section className="tool-page"><div className="section-kicker">CAREER COPILOT</div><h1>One focused <span>week.</span></h1><p>Concrete repository and practice actions derived from your current evidence.</p><button className="primary-btn" onClick={runPlan} disabled={busy}>{busy?"Building…":"Build my 7-day plan →"}</button>{plan&&<div className="plan-list"><p>{plan.summary}</p>{plan.actions.map((x,i)=><div key={i}><b>DAY {i+1}</b><span>{x}</span></div>)}</div>}</section>}
      </main>
    </div>
  </div>
}
function Loading(){return <div className="loading-state"><div className="loader-orb"/><div><div className="section-kicker">GEMINI IS WORKING</div><h2>Reading your engineering evidence…</h2><p>Scanning repositories, extracting signals and composing an assessment tailored to your profile.</p></div></div>}
function JobResult({data}){return <div className="job-result"><h3>Evidence map</h3>{data.requirements.map(r=><div className="req-row" key={r}><span>{r}</span><b>{data.evidence?.[r]||"No evidence"}</b></div>)}<div className="gap-box"><b>Gaps to work on</b>{data.gaps.map((g,i)=><p key={i}>→ {g}</p>)}</div><div className="gap-box"><b>Preparation actions</b>{data.preparation.map((g,i)=><p key={i}>→ {g}</p>)}</div></div>}
