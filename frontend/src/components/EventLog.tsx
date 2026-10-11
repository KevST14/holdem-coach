import { useEffect, useRef } from "react";
import type { GameEvent } from "../api";

export default function EventLog({ events, yourSeat }: { events: GameEvent[]; yourSeat: number }) {
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [events]);

  return (
    <section className="panel log" aria-label="What happened this hand">
      <h2>This hand</h2>
      <ol ref={listRef}>
        {events.map((e, i) => (
          <li key={i} className={`log-${e.kind} ${e.seat === yourSeat ? "mine" : ""}`}>
            {e.text}
          </li>
        ))}
      </ol>
    </section>
  );
}
