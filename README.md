# Hold'em Coach

Learn Texas Hold'em from scratch, then practice against computer opponents with a coach that explains every decision.

- **Learn**: how a hand plays out, hand rankings with examples, and a glossary.
- **Play**: a full no-limit Hold'em table against 1-5 bots with different personalities. The coach shows what your hand is, any draws, your chance of winning, the price of calling, and a suggested move with the reasoning.

## Layout

```
backend/   Python: game engine, bots, coach, FastAPI server
  src/holdem/
    cards.py       cards and decks
    evaluator.py   best five-card hand from 5-7 cards
    pots.py        main pot and side pots
    game.py        the table: blinds, betting rounds, all-ins, showdown
    equity.py      Monte Carlo win-chance estimates
    bots.py        computer opponents
    coach.py       beginner explanations and suggestions
    learn.py       lesson content
    api/           HTTP API (in-memory game sessions)
  tests/
frontend/  React + TypeScript + Vite
```

## Running it

Requires Python 3.11+ with [uv](https://docs.astral.sh/uv/), and Node 20+.

```bash
cd backend && uv sync && uv run uvicorn holdem.api.app:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

Then open http://localhost:5173. The dev server forwards `/api` to the backend on port 8000.

## Tests

```bash
cd backend && uv run pytest
```

```bash
cd frontend && npm run build
```

Games live in memory, so restarting the backend ends any game in progress.
