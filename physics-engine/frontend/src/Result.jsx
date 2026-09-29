// Renders one /solve response per physics_mode_api.json.
// Invariant from the contract: nothing is ever shown under a "verified"
// badge unless the server said verification === "verified".

const STATES = ["verified", "needs_review", "unverified"];

function fmt(v) {
  return typeof v === "number" ? Number(v.toPrecision(5)).toString() : String(v);
}

export default function Result({ data }) {
  // Unknown or missing state is treated as unverified, never as verified.
  const state = STATES.includes(data.verification) ? data.verification : "unverified";
  const answer = data.answer && Object.keys(data.answer).length ? data.answer : null;
  const sources = data.sources && Object.keys(data.sources).length ? data.sources : null;

  return (
    <article className={`result ${state}`}>
      <span className={`badge ${state}`}>{data.badge || "Unverified"}</span>

      {data.needs_llm_completion && (
        <p className="notice">
          The engine could not finish this problem. Any answer from another model
          stays unverified.
        </p>
      )}

      {answer && (
        <div className="answer">
          {Object.entries(answer).map(([k, v]) => (
            <span key={k}><var>{k}</var> = {fmt(v)}</span>
          ))}
        </div>
      )}

      {data.candidates?.length > 0 && (
        <div className="block">
          <h2>More than one principle fits. Pick the one that matches your problem.</h2>
          {data.candidates.map((c, i) => (
            <div className="candidate" key={i}>
              <strong>{c.principle}</strong>
              <div>Applies when: {c.applies_when}</div>
              <div>Gives: {Object.entries(c.answer || {}).map(([k, v]) => `${k} = ${fmt(v)}`).join(", ")}</div>
            </div>
          ))}
        </div>
      )}

      {data.hints?.length > 0 && (
        <div className="block">
          <h2>Hints</h2>
          <ol>{data.hints.map((h, i) => <li key={i}>{h}</li>)}</ol>
        </div>
      )}

      {data.formula_used && <p className="meta">Formula: {data.formula_used}</p>}
      {data.assumptions?.length > 0 && <p className="meta">Assumes: {data.assumptions.join("; ")}</p>}

      {sources && (
        <div className="meta">
          Read from your text:
          <ul>
            {Object.entries(sources).map(([k, phrase]) => (
              <li key={k}><var>{k}</var> from "{phrase}"</li>
            ))}
          </ul>
        </div>
      )}

      {data.explanation && <p className="meta">{data.explanation}</p>}
      {typeof data.latency_ms === "number" && (
        <p className="meta small">{Math.round(data.latency_ms)} ms</p>
      )}
    </article>
  );
}