"""Cards and decks.

Cards use the common two-character notation: rank then suit, e.g. ``As`` is
the Ace of Spades and ``Td`` is the Ten of Diamonds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Sequence

RANK_CHARS = "23456789TJQKA"
SUIT_CHARS = "cdhs"

RANK_NAMES = {
    2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight",
    9: "Nine", 10: "Ten", 11: "Jack", 12: "Queen", 13: "King", 14: "Ace",
}
RANK_PLURALS = {
    2: "Twos", 3: "Threes", 4: "Fours", 5: "Fives", 6: "Sixes", 7: "Sevens", 8: "Eights",
    9: "Nines", 10: "Tens", 11: "Jacks", 12: "Queens", 13: "Kings", 14: "Aces",
}
SUIT_NAMES = {"c": "Clubs", "d": "Diamonds", "h": "Hearts", "s": "Spades"}
SUIT_SYMBOLS = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}


@dataclass(frozen=True, order=True)
class Card:
    rank: int  # 2..14, where 14 is the Ace
    suit: str  # one of "c", "d", "h", "s"

    def __post_init__(self) -> None:
        if self.rank not in RANK_NAMES:
            raise ValueError(f"invalid rank: {self.rank!r}")
        if self.suit not in SUIT_NAMES:
            raise ValueError(f"invalid suit: {self.suit!r}")

    @classmethod
    def parse(cls, text: str) -> Card:
        text = text.strip()
        if len(text) != 2:
            raise ValueError(f"card must be two characters like 'As', got {text!r}")
        rank_char, suit_char = text[0].upper(), text[1].lower()
        if rank_char not in RANK_CHARS:
            raise ValueError(f"invalid rank in {text!r}")
        return cls(RANK_CHARS.index(rank_char) + 2, suit_char)

    @property
    def rank_char(self) -> str:
        return RANK_CHARS[self.rank - 2]

    @property
    def name(self) -> str:
        return f"{RANK_NAMES[self.rank]} of {SUIT_NAMES[self.suit]}"

    @property
    def symbol(self) -> str:
        return f"{self.rank_char}{SUIT_SYMBOLS[self.suit]}"

    def __str__(self) -> str:
        return f"{self.rank_char}{self.suit}"

    def __repr__(self) -> str:
        return f"Card({str(self)!r})"


def parse_cards(text: str) -> list[Card]:
    """Parse ``"As Kd"`` or ``"AsKd"`` into a list of cards."""
    compact = "".join(text.split())
    if len(compact) % 2:
        raise ValueError(f"cannot split {text!r} into two-character cards")
    return [Card.parse(compact[i : i + 2]) for i in range(0, len(compact), 2)]


def full_deck() -> list[Card]:
    return [Card(rank, suit) for suit in SUIT_CHARS for rank in range(2, 15)]
