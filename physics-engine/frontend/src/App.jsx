import { useState } from "react";
import { solve, loadToken, saveToken } from "./api.js";
import Result from "./Result.jsx";

const EXAMPLES = [
  ["Numeric", "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension."],
  ["Symbolic", "Two masses m1 and m2 hang from a frictionless pulley. Find the acceleration and tension."],
  ["Out of scope", "A 0.5 kg mass on a spring with damping constant 1.2 kg/s. Find the damped frequency."],
];

export default function App() {
  const [query, setQuery] = useState("");
  const [render, setRender] = useState("solve");
  const [token, setToken] = useState(loadToken);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultId, setResultId] = useState(0);

  function onToken(e) {
    const t = e.target.value.trim();
    setToken(t);
    saveToken(t);
  }

  async function onSolve() {
    const q = query.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await solve({ query: q, render, token }));
      setResultId((n) => n + 1);   // new key resets the hint ladder
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header>
        <h1>Physics Engine</h1>
        <p className="sub">Every answer says whether it was symbolically verified, or admits it wasn't.</p>
      </header>

      <label className="field">
        <span>Access token</span>
        <input
          type="password"
          value={token}
          onChange={onToken}
          placeholder="Paste a token from mint_token.py"
          autoComplete="off"
          spellCheck="false"
        />
      </label>

      <label className="field">
        <span>Problem</span>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) onSolve(); }}
          placeholder="A car starts from rest and accelerates at 2.5 m/s^2 for 12 s. Find its final speed and distance."
        />
      </label>

      <div className="row">
        <button onClick={onSolve} disabled={loading || !query.trim()}>
          {loading ? "Solving..." : "Solve"}
        </button>
        <select value={render} onChange={(e) => setRender(e.target.value)} aria-label="Output">
          <option value="solve">Show answer</option>
          <option value="tutor">Show hints</option>
        </select>
        <span className="examples">
          Try:
          {EXAMPLES.map(([label, text]) => (
            <button key={label} className="link" onClick={() => setQuery(text)}>{label}</button>
          ))}
        </span>
      </div>

      <section aria-live="polite">
        {error && <ErrorBox error={error} />}
        {result && <Result key={resultId} data={result} />}
      </section>
    </main>
  );
}

function ErrorBox({ error }) {
  const wait = error.kind === "rate" && error.retryAfter ? ` Try again in ${error.retryAfter}s.` : "";
  return <div className="error">{error.message}{wait}</div>;
}