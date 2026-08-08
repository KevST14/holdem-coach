"""Hand evaluation: find the best five-card poker hand from 5 to 7 cards.

``evaluate`` returns a ``HandValue``. Hand values compare directly, so the
larger value wins and equal values split the pot.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Sequence

from holdem.cards import RANK_NAMES, RANK_PLURALS, Card


class HandCategory(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8

    @property
    def label(self) -> str:
        return " ".join(w if w in ("of", "a") else w.capitalize() for w in self.name.lower().split("_"))


@dataclass(frozen=True, order=True)
class HandValue:
    category: HandCategory
    tiebreak: tuple[int, ...]
    cards: tuple[Card, ...] = field(compare=False)  # the best five, most important first

    @property
    def name(self) -> str:
        if self.category is HandCategory.STRAIGHT_FLUSH and self.tiebreak[0] == 14:
            return "Royal Flush"
        return self.category.label

    def describe(self) -> str:
        """Plain-English description, e.g. 'Full House, Kings full of Sevens'."""
        t = self.tiebreak
        match self.category:
            case HandCategory.HIGH_CARD:
                return f"High Card, {RANK_NAMES[t[0]]}"
            case HandCategory.PAIR:
                return f"Pair of {RANK_PLURALS[t[0]]}"
            case HandCategory.TWO_PAIR:
                return f"Two Pair, {RANK_PLURALS[t[0]]} and {RANK_PLURALS[t[1]]}"
            case HandCategory.THREE_OF_A_KIND:
                return f"Three of a Kind, {RANK_PLURALS[t[0]]}"
            case HandCategory.STRAIGHT:
                return f"Straight, {RANK_NAMES[t[0]]} high"
            case HandCategory.FLUSH:
                return f"Flush, {RANK_NAMES[t[0]]} high"
            case HandCategory.FULL_HOUSE:
                return f"Full House, {RANK_PLURALS[t[0]]} full of {RANK_PLURALS[t[1]]}"
            case HandCategory.FOUR_OF_A_KIND:
                return f"Four of a Kind, {RANK_PLURALS[t[0]]}"
            case HandCategory.STRAIGHT_FLUSH:
                if t[0] == 14:
                    return "Royal Flush"
                return f"Straight Flush, {RANK_NAMES[t[0]]} high"
        raise AssertionError(self.category)
