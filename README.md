# Hold'em Coach

[![Tests](https://github.com/KevST14/holdem-coach/actions/workflows/tests.yml/badge.svg)](https://github.com/KevST14/holdem-coach/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Last commit](https://img.shields.io/github/last-commit/KevST14/holdem-coach)

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
