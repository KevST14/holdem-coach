"""Estimate how often a hand wins by dealing out the unknown cards many times."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from holdem.cards import Card, full_deck
from holdem.evaluator import evaluate


@dataclass(frozen=True)
class Equity:
    win: float  # fraction of deals won outright
    tie: float  # fraction of deals split
    share: float  # expected fraction of the pot, counting ties as partial wins


def estimate_equity(
    hole: Sequence[Card],
    board: Sequence[Card] = (),
    opponents: int = 1,
    iterations: int = 400,
    rng: random.Random | None = None,
) -> Equity:
    """Monte Carlo equity of ``hole`` against ``opponents`` random hands."""
    if len(hole) != 2:
        raise ValueError("need exactly two hole cards")
    if len(board) > 5:
        raise ValueError("board has at most five cards")
    if not 1 <= opponents <= 9:
        raise ValueError("opponents must be between 1 and 9")
    rng = rng or random.Random()
    known = set(hole) | set(board)
    unknown = [c for c in full_deck() if c not in known]
    to_board = 5 - len(board)
    needed = 2 * opponents + to_board

    wins = ties = 0
    share = 0.0
    for _ in range(iterations):
        drawn = rng.sample(unknown, needed)
        full_board = [*board, *drawn[:to_board]]
        mine = evaluate([*hole, *full_board])
        theirs = [evaluate([*drawn[to_board + 2 * i : to_board + 2 * i + 2], *full_board]) for i in range(opponents)]
        best = max(theirs)
        if mine > best:
            wins += 1
            share += 1
        elif mine == best:
            ties += 1
            share += 1 / (1 + theirs.count(mine))
    return Equity(win=wins / iterations, tie=ties / iterations, share=share / iterations)
