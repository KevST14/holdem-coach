import { useEffect, useState } from "react";
import { api, type LearnContent } from "../api";
import PlayingCard from "./PlayingCard";

export default function Learn({ onStartPlaying }: { onStartPlaying: () => void }) {
  const [content, setContent] = useState<LearnContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.learn().then(setContent, (e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error" role="alert">Couldn't load lessons: {error}</p>;
  if (!content) return <p className="muted">Loading lessons…</p>;

  const terms = content.glossary.filter(
    (g) => !filter || `${g.term} ${g.definition}`.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="learn">
      <section className="hero">
        <h2>New to poker? Start here.</h2>
        <p>
          In Texas Hold'em, everyone gets <strong>two private cards</strong> and shares <strong>five cards</strong> in
          the middle. You make the best five-card hand you can from those seven. You win chips by having the best hand
          at the end, or by betting so that everyone else gives up first.
        </p>
        <button className="btn primary" onClick={onStartPlaying}>
          Play a practice game
        </button>
      </section>

      <section className="panel">
        <h2>How a hand plays out</h2>
        <ol className="steps">
          {content.steps.map((s) => (
            <li key={s.title}>
              <strong>{s.title}</strong>
              <p>{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <h2>Hand rankings</h2>
        <p className="muted">From strongest to weakest. A hand beats every hand below it.</p>
        <ol className="rankings">
          {content.rankings.map((r, i) => (
            <li key={r.name}>
              <span className="rank-num">{i + 1}</span>
              <div className="rank-cards">
                {r.example.map((c) => (
                  <PlayingCard key={c} card={c} size="sm" />
                ))}
              </div>
              <div className="rank-text">
                <strong>{r.name}</strong>
                <p>{r.explanation}</p>
                <p className="muted small">Example: {r.example_description}. You'll make one {r.odds} hands.</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <header className="panel-head">
          <h2>Glossary</h2>
          <input
            className="search"
            type="search"
            placeholder="Search terms"
            aria-label="Search glossary"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </header>
        <dl className="glossary">
          {terms.map((g) => (
            <div key={g.term}>
              <dt>{g.term}</dt>
              <dd>{g.definition}</dd>
            </div>
          ))}
          {terms.length === 0 && <p className="muted">No terms match "{filter}".</p>}
        </dl>
      </section>
    </div>
  );
}
