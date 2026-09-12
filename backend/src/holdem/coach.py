"""Plain-English help for beginners: what you hold, what each move means,
and a suggested play with the reasoning behind it."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Sequence

from holdem.cards import RANK_NAMES, RANK_PLURALS, Card
from holdem.equity import estimate_equity
from holdem.evaluator import HandCategory, evaluate
from holdem.game import ActionType, Game

SUIT_SINGULAR = {"c": "club", "d": "diamond", "h": "heart", "s": "spade"}


@dataclass(frozen=True)
class HandSummary:
    name: str  # "Pocket Kings", "Pair of Kings", ...
    tip: str
    draws: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActionHelp:
    action: ActionType
    label: str
    explanation: str


@dataclass(frozen=True)
class Coaching:
    hand: HandSummary
    win_chance: float  # 0..1 against the opponents still in the hand
    opponents: int
    price: float | None  # share of the final pot a call needs to win, if facing a bet
    suggestion: ActionType
    reasoning: str
    actions: list[ActionHelp]


# ---------------------------------------------------------------- starting hands

def starting_hand_name(hole: Sequence[Card]) -> str:
    high, low = sorted(hole, key=lambda c: c.rank, reverse=True)
    if high.rank == low.rank:
        return f"Pocket {RANK_PLURALS[high.rank]}"
    suited = "suited" if high.suit == low.suit else "offsuit"
    return f"{RANK_NAMES[high.rank]}-{RANK_NAMES[low.rank]} {suited}"


def chen_score(hole: Sequence[Card]) -> int:
    """Bill Chen's quick starting-hand score: higher is better, 20 is Aces."""
    high, low = sorted(hole, key=lambda c: c.rank, reverse=True)
    points = {14: 10, 13: 8, 12: 7, 11: 6}.get(high.rank, high.rank / 2)
    if high.rank == low.rank:
        return math.ceil(max(points * 2, 5))
    if high.suit == low.suit:
        points += 2
    gap = high.rank - low.rank - 1
    points -= {0: 0, 1: 1, 2: 2, 3: 4}.get(gap, 5)
    if gap <= 1 and high.rank < 12:
        points += 1
    return math.ceil(points)


def starting_hand_tip(hole: Sequence[Card]) -> str:
    score = chen_score(hole)
    if score >= 12:
        return "One of the best starting hands in poker. Raising is usually right."
    if score >= 9:
        return "A strong starting hand. Usually worth playing, often with a raise."
    if score >= 7:
        return "A playable hand that can improve on the flop. Worth playing if it's cheap."
    return "A weak starting hand. Most experienced players fold this unless they can see the flop for free."
