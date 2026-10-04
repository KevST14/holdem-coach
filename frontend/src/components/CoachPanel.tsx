import type { Coach } from "../api";

const ACTION_NAMES = { fold: "Fold", check: "Check", call: "Call", bet: "Bet", raise: "Raise" } as const;

interface Props {
  coach: Coach | null;
  yourHand: string | null;
  visible: boolean;
  onToggle: () => void;
}

export default function CoachPanel({ coach, yourHand, visible, onToggle }: Props) {
  return (
    <section className="panel coach" aria-label="Coach">
      <header className="panel-head">
        <h2>Coach</h2>
        <button className="btn ghost small" onClick={onToggle} aria-pressed={visible}>
          {visible ? "Hide tips" : "Show tips"}
        </button>
      </header>

      {!visible ? (
        <p className="muted">Tips are hidden. Try deciding on your own, then turn them back on to compare.</p>
      ) : !coach ? (
        <>
          {yourHand && (
            <p>
              Your hand: <strong>{yourHand}</strong>
            </p>
          )}
          <p className="muted">The coach weighs in whenever it's your turn.</p>
        </>
      ) : (
        <>
          <div className="coach-block">
            <span className="eyebrow">Your hand</span>
            <strong className="coach-hand">{coach.hand_name}</strong>
            <p>{coach.hand_tip}</p>
            {coach.draws.map((d) => (
              <p key={d} className="draw">
                {d}
              </p>
            ))}
          </div>

          <div className="coach-block">
            <span className="eyebrow">
              Chance to win vs {coach.opponents} opponent{coach.opponents === 1 ? "" : "s"}
            </span>
            <div className="meter" role="img" aria-label={`About ${pct(coach.win_chance)} chance to win`}>
              <div className="meter-fill" style={{ width: pct(coach.win_chance) }} />
              {coach.price !== null && (
                <div className="meter-mark" style={{ left: pct(coach.price) }} title="Needed to call" />
              )}
            </div>
            <div className="meter-legend">
              <span>About {pct(coach.win_chance)}</span>
              {coach.price !== null && <span className="muted">Need {pct(coach.price)} to call</span>}
            </div>
          </div>

          <div className="coach-block suggestion">
            <span className="eyebrow">Suggestion</span>
            <strong>{ACTION_NAMES[coach.suggestion]}</strong>
            <p>{coach.reasoning}</p>
          </div>
        </>
      )}
    </section>
  );
}

function pct(x: number) {
  return `${Math.round(x * 100)}%`;
}
