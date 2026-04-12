import { useState } from "react";
import * as api from "../api";

function LoginScreen({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleStart() {
    if (!username.trim() || !password.trim()) {
      setError("Please enter a username and password.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      // The PvE auth endpoint returns { user: { id, username }, created: bool }
      // There is no token — the user object is passed directly to App.jsx state
      const data = await api.login(username.trim(), password);
      onLoginSuccess(data.user);
    } catch (e) {
      const msg =
        e?.response?.data?.detail ||
        "Login failed — check your username and password.";
      setError(msg);
    }
    setLoading(false);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") handleStart();
  }

  return (
    <div className="login-screen">
      <h1>⚔️ Legends of Sword and Wand</h1>

      <div className="login-form">
        <h2>Sign In</h2>
        <p style={{ color: "#aaa", fontSize: "0.85rem", marginBottom: 8 }}>
          New user? Just enter a username and password to create an account.
        </p>

        <label>Username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter username"
          autoFocus
        />

        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter password"
        />

        {error && <p className="error">{error}</p>}

        <button
          onClick={handleStart}
          disabled={loading}
          className="primary-btn"
        >
          {loading ? "Signing in..." : "Continue"}
        </button>
      </div>
    </div>
  );
}

export default LoginScreen;
