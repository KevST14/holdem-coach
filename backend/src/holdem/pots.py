"""Splitting chips into a main pot and side pots.

When a player is all-in for less than others have bet, they can only win the
chips they could match. Everything above that goes into a side pot that only
the players who put in more are eligible for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Pot:
    amount: int
    eligible: frozenset[int]  # seats that can win this pot


def build_pots(contributions: Mapping[int, int], folded: set[int]) -> list[Pot]:
    """Split total contributions per seat into pots, main pot first.

    Folded players' chips stay in the pots but they are not eligible to win.
    """
    live_levels = sorted({c for seat, c in contributions.items() if seat not in folded and c > 0})
    pots: list[Pot] = []
    previous = 0
    for level in live_levels:
        amount = sum(min(c, level) - min(c, previous) for c in contributions.values())
        eligible = frozenset(s for s, c in contributions.items() if s not in folded and c >= level)
        pots.append(Pot(amount, eligible))
        previous = level
    # Chips a folded player put in above every live player's total belong to the last pot.
    leftover = sum(max(0, c - previous) for c in contributions.values())
    if leftover and pots:
        pots[-1] = Pot(pots[-1].amount + leftover, pots[-1].eligible)
    return pots


def split_pot(amount: int, winners: Sequence[int]) -> dict[int, int]:
    """Split ``amount`` evenly among ``winners``.

    ``winners`` must be ordered starting from the first seat left of the
    button; leftover odd chips go to the earliest winners, as in a card room.
    """
    share, remainder = divmod(amount, len(winners))
    return {seat: share + (1 if i < remainder else 0) for i, seat in enumerate(winners)}
