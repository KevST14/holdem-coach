"""Computer opponents.

Every bot uses the same simple recipe (estimate its chance of winning, compare
it to the price of calling) and a personality that nudges how loose,
aggressive and bluff-happy it is. They're meant to be readable opponents for
beginners, not strong players.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from holdem.equity import estimate_equity
from holdem.game import ActionType, Game, LegalActions, Street


@dataclass(frozen=True)
class Personality:
    name: str
    style: str  # one-line description shown to the player
    looseness: float  # added to its win chance before deciding; > 0 plays more hands
    aggression: float  # chance of betting/raising when it has a good hand
    bluff: float  # chance of betting/raising with a weak hand


PERSONALITIES = [
    Personality("Steady Sam", "Plays solid, sensible poker.", looseness=0.0, aggression=0.6, bluff=0.05),
    Personality("Tense Tina", "Waits patiently for strong hands, then bets them hard.", looseness=-0.08, aggression=0.8, bluff=0.02),
    Personality("Loose Lou", "Loves to play lots of hands and bluffs often.", looseness=0.1, aggression=0.5, bluff=0.18),
    Personality("Calling Carl", "Hates folding and calls almost everything.", looseness=0.25, aggression=0.15, bluff=0.0),
    Personality("Raising Rita", "Bets and raises a lot to put pressure on you.", looseness=0.03, aggression=0.9, bluff=0.12),
]


@dataclass(frozen=True)
class Decision:
    action: ActionType
    amount: int | None = None
    reason: str = ""


class Bot:
    def __init__(self, personality: Personality, rng: random.Random | None = None, iterations: int = 200):
        self.personality = personality
        self.rng = rng or random.Random()
        self.iterations = iterations

    def decide(self, game: Game) -> Decision:
        legal = game.legal_actions()
        me = game.players[legal.seat]
        opponents = sum(p.live for p in game.players) - 1
        equity = estimate_equity(me.hole_cards, game.board, opponents, self.iterations, self.rng).share
        p = self.personality

        fair_share = 1 / (opponents + 1)
        strength = (equity + p.looseness) / fair_share  # 1.0 = an average hand in this spot
        strong = strength >= 1.5
        roll = self.rng.random()
        wants_to_raise = (strong and roll < p.aggression) or roll < p.bluff
        reason = "strong hand" if strong else "bluff"

        if legal.to_call == 0:
            if wants_to_raise and (legal.can_bet or legal.can_raise):
                return self._raise(game, legal, reason)
            return Decision(ActionType.CHECK, reason="nothing worth betting")

        price = legal.to_call / (game.pot + legal.to_call)  # share of the final pot it must win
        if wants_to_raise and legal.can_raise:
            return self._raise(game, legal, reason)
        if equity + p.looseness >= price:
            return Decision(ActionType.CALL, reason="good enough price to call")
        return Decision(ActionType.FOLD, reason="not worth the price")

    def _raise(self, game: Game, legal: LegalActions, reason: str) -> Decision:
        if game.street is Street.PREFLOP:
            target = max(3 * game.current_bet, 3 * game.big_blind)
        elif legal.can_bet:
            target = round(game.pot * self.rng.choice([0.5, 0.66, 0.75]))
        else:
            target = game.current_bet + round(game.pot * 0.75)
        target = max(legal.min_raise_to, min(target, legal.max_raise_to))
        if target >= 0.8 * legal.max_raise_to:
            target = legal.max_raise_to  # close to all-in anyway: just shove
        kind = ActionType.BET if legal.can_bet else ActionType.RAISE
        return Decision(kind, target, reason)
