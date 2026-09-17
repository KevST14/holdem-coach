"""In-memory game sessions: one human against a table of bots."""

from __future__ import annotations

import random
import uuid
from collections import OrderedDict
from dataclasses import dataclass

from holdem.bots import PERSONALITIES, Bot
from holdem.game import Game

MAX_SESSIONS = 200


@dataclass
class Session:
    id: str
    game: Game
    human_seat: int
    bots: dict[int, Bot]
    rng: random.Random

    def run_bots(self) -> None:
        """Let the bots act until it's the human's turn or the hand is over."""
        game = self.game
        while game.in_progress and game.to_act != self.human_seat:
            decision = self.bots[game.to_act].decide(game)
            game.act(decision.action, decision.amount)

    def start_next_hand(self) -> None:
        self.game.start_hand()
        self.run_bots()


class SessionStore:
    def __init__(self) -> None:
        self._sessions: OrderedDict[str, Session] = OrderedDict()

    def create(
        self,
        player_name: str,
        bot_count: int,
        starting_stack: int,
        small_blind: int,
        big_blind: int,
        seed: int | None = None,
    ) -> Session:
        rng = random.Random(seed)
        personalities = rng.sample(PERSONALITIES, bot_count)
        seats = [(player_name, starting_stack, False)] + [(p.name, starting_stack, True) for p in personalities]
        game = Game(seats, small_blind, big_blind, rng=rng, button=rng.randrange(len(seats)))
        bots = {seat: Bot(p, rng=rng) for seat, p in enumerate(personalities, start=1)}
        session = Session(id=uuid.uuid4().hex, game=game, human_seat=0, bots=bots, rng=rng)
        self._sessions[session.id] = session
        while len(self._sessions) > MAX_SESSIONS:
            self._sessions.popitem(last=False)
        session.start_next_hand()
        return session

    def get(self, session_id: str) -> Session:
        session = self._sessions[session_id]
        self._sessions.move_to_end(session_id)
        return session
