"""Lesson content for total beginners: hand rankings, how a hand plays out, and a glossary."""

from __future__ import annotations

from dataclasses import dataclass

from holdem.cards import Card, parse_cards
from holdem.evaluator import evaluate


@dataclass(frozen=True)
class RankingLesson:
    name: str
    example: list[Card]
    explanation: str
    odds: str  # how often you make it by the river with 7 cards

    @property
    def example_description(self) -> str:
        return evaluate(self.example).describe()


HAND_RANKINGS = [
    RankingLesson("Royal Flush", parse_cards("Ah Kh Qh Jh Th"),
                  "A, K, Q, J and 10, all the same suit. The best hand in poker.", "about 1 in 31,000"),
    RankingLesson("Straight Flush", parse_cards("9s 8s 7s 6s 5s"),
                  "Five cards in a row, all the same suit.", "about 1 in 3,600"),
    RankingLesson("Four of a Kind", parse_cards("7c 7d 7h 7s Kd"),
                  "Four cards of the same rank.", "about 1 in 600"),
    RankingLesson("Full House", parse_cards("Kc Kd Ks 7h 7s"),
                  "Three of one rank plus a pair of another.", "about 1 in 38"),
    RankingLesson("Flush", parse_cards("Ac Jc 8c 4c 2c"),
                  "Any five cards of the same suit, not in a row.", "about 1 in 33"),
    RankingLesson("Straight", parse_cards("9c 8d 7h 6s 5c"),
                  "Five cards in a row of mixed suits. An Ace can be high (10-J-Q-K-A) or low (A-2-3-4-5).",
                  "about 1 in 22"),
    RankingLesson("Three of a Kind", parse_cards("Qc Qd Qs 9h 4s"),
                  "Three cards of the same rank.", "about 1 in 21"),
    RankingLesson("Two Pair", parse_cards("Jc Jd 4h 4s Ac"),
                  "Two different pairs.", "about 1 in 4"),
    RankingLesson("Pair", parse_cards("6c 6d Ah Ks 9c"),
                  "Two cards of the same rank.", "about 1 in 2.3"),
    RankingLesson("High Card", parse_cards("Ac Jd 9h 7s 4c"),
                  "Nothing else? Your highest card plays. If tied, compare the next highest.", "about 1 in 6"),
]


HOW_A_HAND_WORKS = [
    ("The blinds",
     "Two players to the left of the dealer button post forced bets called the small blind and big blind. "
     "This puts chips in the pot so there's something to play for."),
    ("Hole cards",
     "Everyone gets two private cards. Only you can see yours."),
    ("Pre-flop betting",
     "Starting left of the big blind, each player folds, calls the big blind, or raises."),
    ("The flop",
     "Three shared cards are dealt face up in the middle. Everyone can use them. Another round of betting follows."),
    ("The turn",
     "A fourth shared card, then another betting round."),
    ("The river",
     "The fifth and final shared card, then the last betting round."),
    ("Showdown",
     "Players still in reveal their cards. Each makes the best five-card hand from their two hole cards plus "
     "the five shared cards. The best hand wins the pot."),
]
