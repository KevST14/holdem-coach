import { useState } from "react";
import type { ActionType, Coach, GameState, Legal } from "../api";

interface Props {
  state: GameState;
  legal: Legal;
  coach: Coach;
  showCoach: boolean;
  busy: boolean;
  onAct: (action: ActionType, amount?: number) => void;
}

export default function ActionBar({ state, legal, coach, showCoach, busy, onAct }: Props) {
  const [amount, setAmount] = useState(legal.min_raise_to);
  const [focused, setFocused] = useState<ActionType | null>(null);
  const help = new Map(coach.actions.map((a) => [a.action, a]));
  const sizingKind: ActionType | null = legal.can_bet ? "bet" : legal.can_raise ? "raise" : null;

  const clamp = (n: number) => Math.round(Math.min(legal.max_raise_to, Math.max(legal.min_raise_to, n)));
  // A "pot-sized" raise: call first, then raise by the size of the pot after calling.
  const potAfterCall = state.pot + legal.to_call;
  const presets = [
    { label: "Min", value: legal.min_raise_to },
    { label: "½ Pot", value: clamp(state.current_bet + potAfterCall / 2) },
    { label: "Pot", value: clamp(state.current_bet + potAfterCall) },
    { label: "All-in", value: legal.max_raise_to },
  ];

  const explained = focused ? help.get(focused) : null;

  function button(action: ActionType, label: string, amountToSend?: number) {
    const suggested = showCoach && coach.suggestion === action;
    return (
      <button
        key={action}
        className={`btn action action-${action} ${suggested ? "suggested" : ""}`}
        disabled={busy}
        onClick={() => onAct(action, amountToSend)}
        onMouseEnter={() => setFocused(action)}
        onFocus={() => setFocused(action)}
        onMouseLeave={() => setFocused(null)}
        onBlur={() => setFocused(null)}
      >
        {label}
        {suggested && <span className="pick">Coach's pick</span>}
      </button>
    );
  }

  return (
    <section className="panel action-bar" aria-label="Your move">
      <h2 className="sr-only">Your move</h2>
      <div className="actions">
        {legal.can_fold && button("fold", "Fold")}
        {legal.can_check && button("check", "Check")}
        {legal.to_call > 0 && button("call", `Call ${legal.to_call}`)}
        {sizingKind && button(sizingKind, `${sizingKind === "bet" ? "Bet" : "Raise to"} ${amount}`, amount)}
      </div>

      {sizingKind && (
        <div className="sizing">
          <input
            type="range"
            aria-label={`${sizingKind} amount`}
            min={legal.min_raise_to}
            max={legal.max_raise_to}
            step={Math.max(1, Math.floor(state.big_blind / 2))}
            value={amount}
            onChange={(e) => setAmount(clamp(Number(e.target.value)))}
          />
          <input
            type="number"
            className="amount"
            aria-label={`${sizingKind} amount`}
            min={legal.min_raise_to}
            max={legal.max_raise_to}
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            onBlur={() => setAmount(clamp(amount))}
          />
          <div className="presets">
            {presets.map((p) => (
              <button key={p.label} className="btn ghost small" onClick={() => setAmount(p.value)} disabled={busy}>
                {p.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <p className="explain" aria-live="polite">
        {explained ? (
          <>
            <strong>{explained.label}:</strong> {explained.explanation}
          </>
        ) : (
          <span className="muted">Hover over or focus a button to see what it does.</span>
        )}
      </p>
    </section>
  );
}
