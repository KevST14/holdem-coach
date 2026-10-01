import type { GameEvent, GameState, Player } from "../api";
import PlayingCard from "./PlayingCard";

const STREET_LABELS: Record<string, string> = {
  preflop: "Pre-flop",
  flop: "Flop",
  turn: "Turn",
  river: "River",
  showdown: "Showdown",
};

function lastAction(events: GameEvent[], seat: number, street: string): string | null {
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.street !== street) break;
    if (e.kind !== "action" || e.seat !== seat) continue;
    switch (e.action) {
      case "fold":
        return "Fold";
      case "check":
        return "Check";
      case "call":
        return `Call ${e.amount}`;
      case "bet":
        return `Bet ${e.amount}`;
      case "raise":
        return `Raise to ${e.amount}`;
    }
  }
  return null;
}

export default function Table({ state }: { state: GameState }) {
  const n = state.players.length;
  const winnings = new Map<number, number>();
  for (const r of state.results) {
    for (const p of r.payouts) winnings.set(p.seat, (winnings.get(p.seat) ?? 0) + p.amount);
  }

  const seat = (p: Player) => {
    // Put you at the bottom and everyone else clockwise around the table, keeping
    // each seat fully inside the table area by shrinking the ellipse by half a seat.
    const position = (p.seat - state.your_seat + n) % n;
    const angle = Math.PI / 2 + (position * 2 * Math.PI) / n;
    const style = {
      left: `calc(50% + ${Math.cos(angle).toFixed(4)} * (50% - var(--seat-half-w)))`,
      top: `calc(50% + ${Math.sin(angle).toFixed(4)} * (50% - var(--seat-half-h)))`,
    };
    return (
      <Seat
        key={p.seat}
        player={p}
        style={style}
        acting={state.to_act === p.seat}
        action={state.in_progress ? lastAction(state.events, p.seat, state.street) : null}
        won={winnings.get(p.seat)}
      />
    );
  };

  return (
    <div className="table-wrap">
      <div className="felt">
        <div className="felt-center">
          <span className="street">
            Hand #{state.hand_number} · {STREET_LABELS[state.street] ?? state.street}
          </span>
          <div className="board" aria-label="Shared cards">
            {Array.from({ length: 5 }, (_, i) =>
              state.board[i] ? <PlayingCard key={i} card={state.board[i]} /> : <PlayingCard key={i} placeholder />,
            )}
          </div>
          <span className="pot">Pot {state.pot}</span>
        </div>
      </div>
      {/* On wide screens seats sit around the felt; on phones opponents stack above it. */}
      <div className="opponents">{state.players.filter((p) => !p.is_you).map(seat)}</div>
      {seat(state.players[state.your_seat])}
    </div>
  );
}

function Seat({
  player: p,
  style,
  acting,
  action,
  won,
}: {
  player: Player;
  style: React.CSSProperties;
  acting: boolean;
  action: string | null;
  won: number | undefined;
}) {
  const out = !p.in_hand;
  const classes = ["seat", p.is_you && "you", acting && "acting", (p.folded || out) && "folded", won && "winner"]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} style={style} title={p.style ?? undefined}>
      <div className="seat-cards">
        {p.in_hand && !p.folded && (p.cards ? p.cards.map((c) => <PlayingCard key={c} card={c} size="sm" />) : (
          <>
            <PlayingCard size="sm" />
            <PlayingCard size="sm" />
          </>
        ))}
      </div>
      <div className="seat-plate">
        <div className="seat-name">
          {p.name}
          {p.is_button && <span className="badge dealer" title="Dealer button">D</span>}
          {p.is_small_blind && <span className="badge" title="Small blind">SB</span>}
          {p.is_big_blind && <span className="badge" title="Big blind">BB</span>}
        </div>
        <div className="seat-stack">{out ? "Out" : `${p.stack} chips`}</div>
      </div>
      <div className="seat-status">
        {won ? (
          <span className="tag win">Won {won}</span>
        ) : p.showdown_hand ? (
          <span className="tag">{p.showdown_hand}</span>
        ) : p.all_in ? (
          <span className="tag allin">All-in</span>
        ) : action ? (
          <span className="tag">{action}</span>
        ) : null}
        {p.bet > 0 && <span className="chip-bet">{p.bet}</span>}
      </div>
    </div>
  );
}
