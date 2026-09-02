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
