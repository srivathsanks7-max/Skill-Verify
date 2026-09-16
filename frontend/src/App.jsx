import { useEffect, useState } from "react";
import { getCurrentUser, logout } from "./api";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    getCurrentUser().then((res) => {
      if (res.logged_in) setUser(res);
    }).catch(() => {}).finally(() => setChecking(false));
  }, []);

  async function handleLogout() {
    await logout();
    setUser(null);
  }

  if (checking) return <div className="loading-screen"><div className="loader-orb" /><span>Loading SkillVerify…</span></div>;
  return user ? <Dashboard user={user} onLogout={handleLogout} /> : <Login />;
}
