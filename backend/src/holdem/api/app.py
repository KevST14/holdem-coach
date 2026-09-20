"""HTTP API for playing against bots.

Run with: uv run uvicorn holdem.api.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from holdem.api.schemas import ActionRequest, GameState, NewGameRequest, game_state, learn_content
from holdem.api.sessions import Session, SessionStore
from holdem.game import IllegalActionError

app = FastAPI(title="Hold'em Coach")
store = SessionStore()


def _session(game_id: str) -> Session:
    try:
        return store.get(game_id)
    except KeyError:
        raise HTTPException(404, "game not found") from None


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/games", response_model=GameState)
def new_game(req: NewGameRequest) -> GameState:
    session = store.create(req.player_name, req.bots, req.starting_stack, req.small_blind, req.big_blind, req.seed)
    return game_state(session)


@app.get("/api/games/{game_id}", response_model=GameState)
def get_game(game_id: str) -> GameState:
    return game_state(_session(game_id))


@app.post("/api/games/{game_id}/actions", response_model=GameState)
def take_action(game_id: str, req: ActionRequest) -> GameState:
    session = _session(game_id)
    game = session.game
    if not game.in_progress or game.to_act != session.human_seat:
        raise HTTPException(409, "it's not your turn")
    try:
        game.act(req.action, req.amount)
    except IllegalActionError as e:
        raise HTTPException(400, str(e)) from None
    session.run_bots()
    return game_state(session)
