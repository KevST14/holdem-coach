import { useState } from "react";
import { api, type ActionType, type GameState, type NewGameSettings } from "../api";
import ActionBar from "./ActionBar";
import CoachPanel from "./CoachPanel";
import EventLog from "./EventLog";
import Table from "./Table";

export default function Play() {
  const [state, setState] = useState<GameState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCoach, setShowCoach] = useState(true);

  async function run(call: () => Promise<GameState>) {
    setBusy(true);
    setError(null);
    try {
      setState(await call());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!state) {
    return <NewGameForm busy={busy} error={error} onStart={(s) => run(() => api.newGame(s))} />;
  }

  const act = (action: ActionType, amount?: number) => run(() => api.act(state.id, action, amount));

  return (
    <div className="play">
      <div className="play-main">
        <Table state={state} />
        {error && (
          <div className="error row" role="alert">
            <span>{error === "game not found" ? "This game is no longer on the server (it may have restarted)." : error}</span>
            {error === "game not found" && (
              <button className="btn small" onClick={() => { setError(null); setState(null); }}>
                Start a new game
              </button>
            )}
          </div>
        )}
        {state.your_turn && state.legal && state.coach ? (
          <ActionBar
            key={`${state.hand_number}-${state.events.length}`}
            state={state}
            legal={state.legal}
            coach={state.coach}
            showCoach={showCoach}
            busy={busy}
            onAct={act}
          />
        ) : (
          <HandResult
            state={state}
            busy={busy}
            onNextHand={() => run(() => api.nextHand(state.id))}
            onNewGame={() => setState(null)}
          />
        )}
      </div>
      <aside className="play-side">
        <CoachPanel
          coach={state.coach}
          yourHand={state.your_hand}
          visible={showCoach}
          onToggle={() => setShowCoach((v) => !v)}
        />
        <EventLog events={state.events} yourSeat={state.your_seat} />
      </aside>
    </div>
  );
}

function NewGameForm({
  busy,
  error,
  onStart,
}: {
  busy: boolean;
  error: string | null;
  onStart: (settings: NewGameSettings) => void;
}) {
  const [name, setName] = useState("Player");
  const [bots, setBots] = useState(3);

  return (
    <form
      className="panel new-game"
      onSubmit={(e) => {
        e.preventDefault();
        onStart({ player_name: name.trim() || "Player", bots, starting_stack: 1000, small_blind: 5, big_blind: 10 });
      }}
    >
      <h2>Start a practice game</h2>
      <p className="muted">
        Play Texas Hold'em against computer opponents. Everyone starts with 1,000 chips and the blinds are 5 and 10.
        The coach explains every decision as you go.
      </p>
      <label>
        Your name
        <input value={name} maxLength={20} onChange={(e) => setName(e.target.value)} />
      </label>
      <label>
        Opponents: <strong>{bots}</strong>
        <input type="range" min={1} max={5} value={bots} onChange={(e) => setBots(Number(e.target.value))} />
      </label>
      <p className="muted small">Fewer opponents makes it easier to follow what's happening.</p>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="btn primary" type="submit" disabled={busy}>
        {busy ? "Shuffling…" : "Deal me in"}
      </button>
    </form>
  );
}

function HandResult({
  state,
  busy,
  onNextHand,
  onNewGame,
}: {
  state: GameState;
  busy: boolean;
  onNextHand: () => void;
  onNewGame: () => void;
}) {
  const wins = state.events.filter((e) => e.kind === "win");
  const you = state.players[state.your_seat];
  const youWon = state.results.some((r) => r.payouts.some((p) => p.seat === state.your_seat));
  const everyoneElseBroke = state.players.every((p) => p.is_you || p.stack === 0);

  return (
    <section className={`panel result ${youWon ? "won" : ""}`} aria-live="polite">
      <h2>{youWon ? "You won!" : "Hand over"}</h2>
      {wins.map((e, i) => (
        <p key={i}>{e.text}</p>
      ))}
      {state.game_over ? (
        <>
          <p>
            <strong>
              {everyoneElseBroke ? "You won every chip at the table. Nicely played!" : "You're out of chips. Game over."}
            </strong>
          </p>
          <button className="btn primary" onClick={onNewGame}>
            New game
          </button>
        </>
      ) : (
        <div className="row">
          <span className="muted">Your stack: {you.stack}</span>
          <button className="btn primary" onClick={onNextHand} disabled={busy} autoFocus>
            {busy ? "Dealing…" : "Deal next hand"}
          </button>
        </div>
      )}
    </section>
  );
}
