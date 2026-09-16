export default function SkillProfile({ profile }) {
  const skills = Object.entries(profile?.skills || {});
  return <aside className="sidebar">
    <div className="sidebar-top"><div className="mini-label">EVIDENCE PROFILE</div><span className="live-dot">● LIVE</span></div>
    {!profile ? <div className="sidebar-empty"><div className="pulse-ring">✦</div><p>Run an assessment to turn your repository activity into an evidence-backed profile.</p></div> :
      <>
        <div className="skill-list">{skills.map(([skill, level], i) => <div className="skill-item" key={skill}>
          <div><span className="skill-rank">0{i+1}</span><strong>{skill}</strong></div><span className={`level-pill ${level}`}>{level}</span>
        </div>)}</div>
        <p className="profile-note">{profile.notes}</p>
        <div className="freshness"><span>Verification shelf life</span><b>90 days</b></div>
      </>}
  </aside>;
}
