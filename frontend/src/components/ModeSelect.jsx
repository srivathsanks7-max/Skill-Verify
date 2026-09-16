import { useState } from "react";

export default function ModeSelect({ onStart }) {
  const [sourceMode, setSourceMode] = useState("github");
  const [assessmentMode, setAssessmentMode] = useState("adaptive");
  const [resumeText, setResumeText] = useState("");

  const cards = [
    ["adaptive", "⚡", "Adaptive verification", "GitHub + coding + debugging + code review", "Recommended flow"],
    ["debug", "🐞", "Debug my own code", "Fix a realistic bug grounded in your repositories", "Anti-copy challenge"],
    ["review", "🔎", "Code review", "Find correctness, security and maintainability issues", "Engineering skill"],
    ["coding", "⌘", "Targeted coding", "Classic coding questions selected from your evidence", "Focused practice"],
  ];

  return <section className="mode-select">
    <div className="section-kicker">YOUR TECHNICAL CAREER COPILOT</div>
    <h1>What should we verify <span>today?</span></h1>
    <p className="section-sub">Start from your GitHub evidence, then verify the skills that matter instead of taking a generic test.</p>

    <div className="source-switch">
      <button className={sourceMode === "github" ? "selected" : ""} onClick={() => setSourceMode("github")}>◉ Analyze GitHub</button>
      <button className={sourceMode === "manual" ? "selected" : ""} onClick={() => setSourceMode("manual")}>✎ Self-report skills</button>
    </div>

    {sourceMode === "github" && <textarea className="resume-box" placeholder="Optional: paste resume text so we can compare claimed vs evidence-backed skills…" value={resumeText} onChange={e => setResumeText(e.target.value)} />}

    <div className="mode-grid">
      {cards.map(([id, icon, title, desc, tag]) =>
        <button key={id} className={`mode-card ${assessmentMode === id ? "chosen" : ""}`} onClick={() => setAssessmentMode(id)}>
          <div className="mode-icon">{icon}</div>
          <div className="mode-tag">{tag}</div>
          <h3>{title}</h3><p>{desc}</p><span>{assessmentMode === id ? "Selected ✓" : "Choose →"}</span>
        </button>
      )}
    </div>

    {sourceMode === "manual" && <ManualSkills onStart={payload => onStart({source_mode:"manual", assessment_mode:assessmentMode, ...payload})} />}
    {sourceMode === "github" && <button className="primary-btn launch-btn" onClick={() => onStart({source_mode:"github", assessment_mode:assessmentMode, resume_text:resumeText, language:"python"})}>Build my assessment <span>→</span></button>}
  </section>;
}

function ManualSkills({ onStart }) {
  const [value, setValue] = useState("Python, intermediate\nReact, intermediate\nSQL, beginner");
  return <div className="manual-launch">
    <textarea className="resume-box" value={value} onChange={e => setValue(e.target.value)} />
    <button className="primary-btn" onClick={() => {
      const skills = {};
      value.split("\n").forEach(line => {
        const [skill, level="intermediate"] = line.split(",").map(x => x.trim());
        if (skill) skills[skill.toLowerCase()] = level;
      });
      onStart({skills});
    }}>Generate from these skills <span>→</span></button>
  </div>;
}
