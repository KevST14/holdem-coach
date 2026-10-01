const SUITS: Record<string, { symbol: string; name: string; red: boolean }> = {
  c: { symbol: "♣", name: "Clubs", red: false },
  d: { symbol: "♦", name: "Diamonds", red: true },
  h: { symbol: "♥", name: "Hearts", red: true },
  s: { symbol: "♠", name: "Spades", red: false },
};

const RANK_NAMES: Record<string, string> = {
  T: "Ten", J: "Jack", Q: "Queen", K: "King", A: "Ace",
  "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine",
};

interface Props {
  card?: string; // e.g. "As"; omit for a face-down card
  size?: "sm" | "md" | "lg";
  placeholder?: boolean;
}

export default function PlayingCard({ card, size = "md", placeholder }: Props) {
  if (placeholder) return <div className={`card card-${size} card-slot`} aria-hidden="true" />;
  if (!card) return <div className={`card card-${size} card-back`} aria-label="Face-down card" />;

  const rank = card[0];
  const suit = SUITS[card[1]];
  const label = `${RANK_NAMES[rank]} of ${suit.name}`;
  return (
    <div className={`card card-${size} ${suit.red ? "red" : "black"}`} aria-label={label} title={label}>
      <span className="card-rank">{rank === "T" ? "10" : rank}</span>
      <span className="card-suit">{suit.symbol}</span>
    </div>
  );
}
