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


def _by_rank_desc(cards: Sequence[Card]) -> list[Card]:
    return sorted(cards, key=lambda c: c.rank, reverse=True)


def _find_straight(cards: Sequence[Card]) -> list[Card] | None:
    """Return the highest five-card straight in ``cards``, high card first."""
    by_rank: dict[int, Card] = {}
    for card in cards:
        by_rank.setdefault(card.rank, card)
    if 14 in by_rank:
        by_rank[1] = by_rank[14]  # the Ace also plays low: A-2-3-4-5 (the "wheel")
    for high in range(14, 4, -1):
        run = [by_rank.get(r) for r in range(high, high - 5, -1)]
        if all(run):
            return run  # type: ignore[return-value]
    return None


def evaluate(cards: Sequence[Card]) -> HandValue:
    """Evaluate the best five-card hand that can be made from 5-7 cards."""
    if not 5 <= len(cards) <= 7:
        raise ValueError(f"need 5 to 7 cards, got {len(cards)}")
    if len(set(cards)) != len(cards):
        raise ValueError("duplicate cards")

    by_suit: dict[str, list[Card]] = defaultdict(list)
    for card in cards:
        by_suit[card.suit].append(card)
    flush = next((_by_rank_desc(s) for s in by_suit.values() if len(s) >= 5), None)

    if flush:
        straight_flush = _find_straight(flush)
        if straight_flush:
            return HandValue(HandCategory.STRAIGHT_FLUSH, (_high(straight_flush),), tuple(straight_flush))

    by_rank: dict[int, list[Card]] = defaultdict(list)
    for card in _by_rank_desc(cards):
        by_rank[card.rank].append(card)
    # Biggest groups first; among equal-sized groups, higher rank first.
    groups = sorted(by_rank.values(), key=lambda g: (len(g), g[0].rank), reverse=True)

    def kickers(used: list[Card], count: int) -> list[Card]:
        return [c for c in _by_rank_desc(cards) if c not in used][:count]

    top = groups[0]
    if len(top) == 4:
        best = top + kickers(top, 1)
        return HandValue(HandCategory.FOUR_OF_A_KIND, (top[0].rank, best[4].rank), tuple(best))

    if len(top) == 3:
        pairs = [g for g in groups[1:] if len(g) >= 2]
        if pairs:
            pair = max(pairs, key=lambda g: g[0].rank)[:2]
            return HandValue(HandCategory.FULL_HOUSE, (top[0].rank, pair[0].rank), tuple(top + pair))

    if flush:
        best = flush[:5]
        return HandValue(HandCategory.FLUSH, tuple(c.rank for c in best), tuple(best))

    straight = _find_straight(cards)
    if straight:
        return HandValue(HandCategory.STRAIGHT, (_high(straight),), tuple(straight))

    if len(top) == 3:
        best = top + kickers(top, 2)
        return HandValue(HandCategory.THREE_OF_A_KIND, tuple(c.rank for c in (best[0], best[3], best[4])), tuple(best))

    if len(top) == 2 and len(groups[1]) == 2:
        made = groups[0] + groups[1]
        best = made + kickers(made, 1)
        return HandValue(HandCategory.TWO_PAIR, (groups[0][0].rank, groups[1][0].rank, best[4].rank), tuple(best))

    if len(top) == 2:
        best = top + kickers(top, 3)
        return HandValue(HandCategory.PAIR, (top[0].rank, *(c.rank for c in best[2:])), tuple(best))

    best = _by_rank_desc(cards)[:5]
    return HandValue(HandCategory.HIGH_CARD, tuple(c.rank for c in best), tuple(best))


def _high(straight: list[Card]) -> int:
    """High card of a straight; the wheel (A-2-3-4-5) is Five high."""
    return 5 if straight[0].rank == 5 else straight[0].rank
