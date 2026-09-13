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


# ---------------------------------------------------------------- made hands and draws

def _straight_completions(cards: Sequence[Card], hole: Sequence[Card]) -> int:
    """How many different ranks would complete a straight that uses a hole card."""
    def with_low_ace(ranks: set[int]) -> set[int]:
        return ranks | {1} if 14 in ranks else ranks

    ranks = {c.rank for c in cards}
    hole_ranks = with_low_ace({c.rank for c in hole})
    count = 0
    for extra in range(2, 15):
        if extra in ranks:
            continue
        candidate = with_low_ace(ranks | {extra})
        for high in range(14, 4, -1):
            run = set(range(high - 4, high + 1))
            if run <= candidate and run & hole_ranks:
                count += 1
                break
    return count


def find_draws(hole: Sequence[Card], board: Sequence[Card]) -> list[str]:
    if not 3 <= len(board) <= 4:
        return []
    cards = [*hole, *board]
    if evaluate(cards).category >= HandCategory.STRAIGHT:
        return []
    cards_to_come = 5 - len(board)
    multiplier = 4 if cards_to_come == 2 else 2
    draws = []
    for suit, name in SUIT_SINGULAR.items():
        suited = [c for c in cards if c.suit == suit]
        if len(suited) == 4 and any(c.suit == suit for c in hole):
            draws.append(f"Flush draw: one more {name} makes a flush. 9 cards help you, "
                         f"roughly {9 * multiplier}% to hit by the river.")
    completions = _straight_completions(cards, hole)
    if completions >= 2:
        draws.append(f"Open-ended straight draw: 8 cards complete your straight, roughly {8 * multiplier}%.")
    elif completions == 1:
        draws.append(f"Gutshot straight draw: only 4 cards complete your straight, roughly {4 * multiplier}%.")
    return draws


def describe_hand(hole: Sequence[Card], board: Sequence[Card]) -> HandSummary:
    if not board:
        return HandSummary(starting_hand_name(hole), starting_hand_tip(hole))

    value = evaluate([*hole, *board])
    draws = find_draws(hole, board)
    board_ranks = sorted((c.rank for c in board), reverse=True)

    if len(board) == 5 and value == evaluate(board):
        tip = "Your best five cards are all on the board, so everyone still in the hand shares at least this."
    elif value.category is HandCategory.HIGH_CARD:
        tip = "You haven't made a pair yet. High-card hands rarely win at showdown."
    elif value.category is HandCategory.PAIR:
        pair = value.tiebreak[0]
        hole_ranks = [c.rank for c in hole]
        if hole_ranks[0] == hole_ranks[1] and pair > board_ranks[0]:
            tip = "An overpair: your pocket pair is higher than every card on the board. Usually a good hand."
        elif pair == board_ranks[0] and pair in hole_ranks:
            tip = "Top pair: you paired the highest card on the board. Often the best hand against one or two players."
        elif pair in hole_ranks:
            tip = "A pair, but not the highest possible. Be careful if someone bets big."
        else:
            tip = "The pair is on the board, so everyone has it. Your other cards decide who wins."
    elif value.category is HandCategory.TWO_PAIR:
        tip = "Two pair is a strong hand that often wins against one or two opponents."
    elif value.category is HandCategory.THREE_OF_A_KIND:
        tip = "Three of a kind is very strong. Betting makes opponents pay to chase you."
    else:
        tip = "A monster hand! Bet to build a big pot."
    return HandSummary(value.describe(), tip, draws)


# ---------------------------------------------------------------- the coach

def explain_actions(game: Game) -> list[ActionHelp]:
    legal = game.legal_actions()
    me = game.players[legal.seat]
    helps = []
    if legal.can_fold:
        lost = f"You lose the {me.contributed} chips you've put in, but" if me.contributed else "You"
        helps.append(ActionHelp(ActionType.FOLD, "Fold", f"Give up this hand. {lost} risk nothing more."))
    if legal.can_check:
        helps.append(ActionHelp(ActionType.CHECK, "Check",
                                "Stay in without adding chips. You can only check when nobody has bet this round."))
    if legal.can_call:
        all_in = " This puts all your chips in." if legal.to_call == me.stack else ""
        helps.append(ActionHelp(ActionType.CALL, f"Call {legal.to_call}",
                                f"Put in {legal.to_call} more to match the bet of {game.current_bet} and stay in.{all_in}"))
    if legal.can_bet:
        helps.append(ActionHelp(ActionType.BET, "Bet",
                                f"Be the first to put chips in this round: from {legal.min_raise_to} up to "
                                f"{legal.max_raise_to} (all-in). Others must match it or fold."))
    if legal.can_raise:
        helps.append(ActionHelp(ActionType.RAISE, "Raise",
                                f"Make the bet bigger: raise to at least {legal.min_raise_to}, up to "
                                f"{legal.max_raise_to} (all-in). Everyone else must match it or fold."))
    return helps


def coach(game: Game, iterations: int = 400, rng: random.Random | None = None) -> Coaching:
    """Coaching for the player whose turn it is."""
    legal = game.legal_actions()
    me = game.players[legal.seat]
    opponents = sum(p.live for p in game.players) - 1
    win = estimate_equity(me.hole_cards, game.board, opponents, iterations, rng).share
    strength = win * (opponents + 1)  # 1.0 means an average hand against this many players
    chance = f"You win about {win:.0%} of the time against {opponents} opponent{'s' if opponents > 1 else ''}"
    aggressive = ActionType.BET if legal.can_bet else ActionType.RAISE

    price = None
    if legal.to_call == 0:
        if strength >= 1.5 and (legal.can_bet or legal.can_raise):
            suggestion = aggressive
            reasoning = f"{chance}, well above average. Betting builds the pot while you're ahead."
        else:
            suggestion = ActionType.CHECK
            reasoning = f"{chance}. Checking is free, so there's no need to put in more chips."
    else:
        price = legal.to_call / (game.pot + legal.to_call)
        cost = (f"Calling costs {legal.to_call} to win a pot of {game.pot + legal.to_call}, "
                f"so you need to win at least {price:.0%} of the time to make it worthwhile")
        if strength >= 1.8 and legal.can_raise:
            suggestion = ActionType.RAISE
            reasoning = f"{chance}, which is very strong. Raising makes others pay more to keep playing."
        elif win >= price:
            suggestion = ActionType.CALL
            reasoning = f"{cost}. {chance}, so calling pays off over time."
        else:
            suggestion = ActionType.FOLD
            reasoning = f"{cost}. {chance}, so folding saves chips in the long run."
    return Coaching(
        hand=describe_hand(me.hole_cards, game.board),
        win_chance=win,
        opponents=opponents,
        price=price,
        suggestion=suggestion,
        reasoning=reasoning,
        actions=explain_actions(game),
    )
