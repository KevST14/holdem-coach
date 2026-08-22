"""No-limit Texas Hold'em table: blinds, betting rounds, side pots, showdown.

A ``Game`` is a table of seated players that plays one hand at a time::

    game = Game([("You", 1000), ("Bot", 1000)], small_blind=5, big_blind=10)
    game.start_hand()
    while game.in_progress:
        legal = game.legal_actions()
        game.act(ActionType.CALL if legal.to_call else ActionType.CHECK)

Bet and raise amounts are always "raise to" totals for the current street,
not the extra chips added. Every step is recorded in ``game.events`` as plain
English so a beginner can follow along.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable, Sequence

from holdem.cards import Card, Deck
from holdem.evaluator import HandValue, evaluate
from holdem.pots import build_pots, split_pot


class Street(StrEnum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class ActionType(StrEnum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


class IllegalActionError(ValueError):
    pass


@dataclass
class Player:
    seat: int
    name: str
    stack: int
    is_bot: bool = False
    hole_cards: list[Card] = field(default_factory=list)
    bet: int = 0  # chips put in on the current street
    contributed: int = 0  # chips put in during the whole hand
    in_hand: bool = False  # was dealt into the current hand
    folded: bool = False
    all_in: bool = False
    has_acted: bool = False  # acted since the last full bet or raise
    can_raise: bool = True  # False after a short all-in raise that doesn't reopen betting

    @property
    def live(self) -> bool:
        """Still contesting the pot."""
        return self.in_hand and not self.folded

    @property
    def active(self) -> bool:
        """Still able to make betting decisions."""
        return self.live and not self.all_in


@dataclass(frozen=True)
class LegalActions:
    seat: int
    can_fold: bool
    can_check: bool
    to_call: int  # chips needed to call; 0 when checking is possible
    can_bet: bool  # open the betting (nobody has bet this street)
    can_raise: bool  # raise an existing bet
    min_raise_to: int  # smallest legal bet/raise total (or all-in if smaller)
    max_raise_to: int  # all-in total

    @property
    def can_call(self) -> bool:
        return self.to_call > 0


@dataclass(frozen=True)
class Event:
    kind: str  # hand_start, blind, deal, action, street, uncalled, show, win, bust
    text: str
    seat: int | None = None
    amount: int | None = None
    action: ActionType | None = None
    street: Street | None = None
    cards: tuple[Card, ...] = ()


@dataclass(frozen=True)
class PotResult:
    amount: int
    payouts: dict[int, int]  # seat -> chips won
    hand: str | None  # winning hand description; None if everyone else folded
    label: str  # "the pot", "the main pot", "side pot 1", ...


class Game:
    def __init__(
        self,
        players: Sequence[tuple[str, int] | tuple[str, int, bool]],
        small_blind: int,
        big_blind: int,
        rng: random.Random | None = None,
        button: int = 0,
    ):
        if not 2 <= len(players) <= 10:
            raise ValueError("a table needs 2 to 10 players")
        if not 0 < small_blind <= big_blind:
            raise ValueError("blinds must satisfy 0 < small blind <= big blind")
        self.players = [
            Player(seat=i, name=p[0], stack=p[1], is_bot=bool(p[2]) if len(p) > 2 else False)
            for i, p in enumerate(players)
        ]
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.rng = rng or random.Random()
        self.button = button
        self.sb_seat: int | None = None
        self.bb_seat: int | None = None
        self.hand_number = 0
        self.street = Street.PREFLOP
        self.board: list[Card] = []
        self.deck = Deck(rng=self.rng)
        self.current_bet = 0
        self.last_raise_size = big_blind
        self.to_act: int | None = None
        self.in_progress = False
        self.events: list[Event] = []
        self.results: list[PotResult] = []
        self.showdown_hands: dict[int, HandValue] = {}

    # ------------------------------------------------------------------ queries

    @property
    def pot(self) -> int:
        """All chips put in this hand, including bets on the current street."""
        return sum(p.contributed for p in self.players)

    @property
    def players_with_chips(self) -> list[Player]:
        return [p for p in self.players if p.stack > 0]

    @property
    def is_over(self) -> bool:
        """True when fewer than two players have chips left."""
        return not self.in_progress and len(self.players_with_chips) < 2

    def seats_after(self, seat: int) -> list[int]:
        """All seats in clockwise order, starting with the one left of ``seat``."""
        n = len(self.players)
        return [(seat + i) % n for i in range(1, n + 1)]

    def _next_seat(self, after: int, predicate: Callable[[Player], bool]) -> int | None:
        return next((s for s in self.seats_after(after) if predicate(self.players[s])), None)

    def legal_actions(self) -> LegalActions:
        if self.to_act is None:
            raise IllegalActionError("no one is due to act")
        p = self.players[self.to_act]
        to_call = min(self.current_bet - p.bet, p.stack)
        max_to = p.bet + p.stack
        anyone_to_respond = any(q.active for q in self.players if q is not p)
        may_raise = p.can_raise and anyone_to_respond and max_to > self.current_bet
        opening = self.current_bet == 0
        return LegalActions(
            seat=p.seat,
            can_fold=to_call > 0,
            can_check=to_call == 0,
            to_call=to_call,
            can_bet=may_raise and opening,
            can_raise=may_raise and not opening,
            min_raise_to=min(self.current_bet + self.last_raise_size, max_to),
            max_raise_to=max_to,
        )

    # ------------------------------------------------------------------ hand flow

    def start_hand(self, deck: Deck | None = None) -> None:
        if self.in_progress:
            raise IllegalActionError("the current hand is not finished")
        if len(self.players_with_chips) < 2:
            raise IllegalActionError("need at least two players with chips")

        for p in self.players:
            p.hole_cards = []
            p.bet = p.contributed = 0
            p.in_hand = p.stack > 0
            p.folded = p.all_in = p.has_acted = False
            p.can_raise = True

        if self.hand_number == 0:
            if not self.players[self.button].in_hand:
                self.button = self._next_seat(self.button, lambda p: p.in_hand)  # type: ignore[assignment]
        else:
            self.button = self._next_seat(self.button, lambda p: p.in_hand)  # type: ignore[assignment]

        self.hand_number += 1
        self.deck = deck or Deck(rng=self.rng)
        self.board = []
        self.events = []
        self.results = []
        self.showdown_hands = {}
        self.street = Street.PREFLOP
        self.in_progress = True

        dealer = self.players[self.button]
        self._log("hand_start", f"Hand #{self.hand_number} begins. {dealer.name} has the dealer button.", seat=dealer.seat)

        dealt_in = [s for s in self.seats_after(self.button) if self.players[s].in_hand]
        if len(dealt_in) == 2:
            # Heads-up: the dealer posts the small blind and acts first before the flop.
            self.sb_seat, self.bb_seat = self.button, dealt_in[0]
        else:
            self.sb_seat, self.bb_seat = dealt_in[0], dealt_in[1]
        self._post_blind(self.players[self.sb_seat], self.small_blind, "small blind")
        self._post_blind(self.players[self.bb_seat], self.big_blind, "big blind")
        self.current_bet = self.big_blind
        self.last_raise_size = self.big_blind

        for seat in dealt_in:
            self.players[seat].hole_cards = self.deck.deal(2)
        self._log("deal", "Each player is dealt two private cards, called hole cards.")

        self.to_act = self._next_seat(self.bb_seat, self._needs_action)
        if self.to_act is None:
            self._end_betting_round()

    def act(self, action: ActionType | str, amount: int | None = None) -> None:
        action = ActionType(action)
        legal = self.legal_actions()
        p = self.players[legal.seat]

        match action:
            case ActionType.FOLD:
                if not legal.can_fold:
                    raise IllegalActionError("no need to fold: you can check for free")
                p.folded = True
                self._log("action", f"{p.name} folds.", seat=p.seat, action=action)
            case ActionType.CHECK:
                if not legal.can_check:
                    raise IllegalActionError(f"cannot check: {legal.to_call} to call")
                self._log("action", f"{p.name} checks.", seat=p.seat, action=action)
            case ActionType.CALL:
                if not legal.can_call:
                    raise IllegalActionError("nothing to call: check instead")
                self._put_in(p, legal.to_call)
                self._log("action", f"{p.name} calls {legal.to_call}{self._all_in_suffix(p)}.",
                          seat=p.seat, amount=legal.to_call, action=action)
            case ActionType.BET | ActionType.RAISE:
                allowed = legal.can_bet if action is ActionType.BET else legal.can_raise
                if not allowed:
                    raise IllegalActionError(f"cannot {action} now")
                if amount is None or not legal.min_raise_to <= amount <= legal.max_raise_to:
                    raise IllegalActionError(
                        f"{action} must be to between {legal.min_raise_to} and {legal.max_raise_to}"
                    )
                self._raise_to(p, amount)
                verb = "bets" if action is ActionType.BET else "raises to"
                self._log("action", f"{p.name} {verb} {amount}{self._all_in_suffix(p)}.",
                          seat=p.seat, amount=amount, action=action)

        p.has_acted = True
        if sum(q.live for q in self.players) == 1:
            self._win_uncontested()
            return
        self.to_act = self._next_seat(p.seat, self._needs_action)
        if self.to_act is None:
            self._end_betting_round()

    # ------------------------------------------------------------------ internals

    def _log(self, kind: str, text: str, **details) -> None:
        self.events.append(Event(kind=kind, text=text, street=self.street, **details))

    @staticmethod
    def _all_in_suffix(p: Player) -> str:
        return " and is all-in" if p.all_in else ""

    def _put_in(self, p: Player, chips: int) -> None:
        p.stack -= chips
        p.bet += chips
        p.contributed += chips
        if p.stack == 0:
            p.all_in = True

    def _post_blind(self, p: Player, amount: int, label: str) -> None:
        chips = min(amount, p.stack)
        self._put_in(p, chips)
        self._log("blind", f"{p.name} posts the {label} of {chips}{self._all_in_suffix(p)}.", seat=p.seat, amount=chips)

    def _raise_to(self, p: Player, total: int) -> None:
        raise_size = total - self.current_bet
        self._put_in(p, total - p.bet)
        full_raise = raise_size >= self.last_raise_size
        for q in self.players:
            if q is p or not q.active:
                continue
            if full_raise:
                q.has_acted, q.can_raise = False, True
            elif q.has_acted:
                # A short all-in raise: players who already acted must respond,
                # but it doesn't reopen the betting for them.
                q.has_acted, q.can_raise = False, False
        if full_raise:
            self.last_raise_size = raise_size
        self.current_bet = total

    def _needs_action(self, p: Player) -> bool:
        if not p.active:
            return False
        if p.bet < self.current_bet:
            return True
        return not p.has_acted and any(q.active for q in self.players if q is not p)

    def _return_uncalled_bet(self) -> None:
        by_bet = sorted(self.players, key=lambda q: q.bet, reverse=True)
        top, runner_up = by_bet[0], by_bet[1]
        excess = top.bet - runner_up.bet
        if excess > 0:
            top.bet -= excess
            top.contributed -= excess
            top.stack += excess
            top.all_in = False
            self._log("uncalled", f"Nobody matched the last {excess} chips, so they go back to {top.name}.",
                      seat=top.seat, amount=excess)

    def _end_betting_round(self) -> None:
        self._return_uncalled_bet()
        for p in self.players:
            p.bet = 0
            p.has_acted = False
            p.can_raise = True
        self.current_bet = 0
        self.last_raise_size = self.big_blind
        self.to_act = None

        while self.street is not Street.RIVER:
            self._deal_next_street()
            if sum(p.active for p in self.players) >= 2:
                self.to_act = self._next_seat(self.button, self._needs_action)
                return
            # Everyone left (but at most one player) is all-in: no more betting,
            # just deal the remaining cards.
        self._showdown()

    def _deal_next_street(self) -> None:
        self.deck.deal(1)  # burn a card face down
        if self.street is Street.PREFLOP:
            self.street, cards = Street.FLOP, self.deck.deal(3)
        elif self.street is Street.FLOP:
            self.street, cards = Street.TURN, self.deck.deal(1)
        else:
            self.street, cards = Street.RIVER, self.deck.deal(1)
        self.board.extend(cards)
        shown = " ".join(c.symbol for c in cards)
        self._log("street", f"{self.street.title()}: {shown}", cards=tuple(cards))

    def _winners_in_button_order(self, seats: Sequence[int]) -> list[int]:
        order = self.seats_after(self.button)
        return sorted(seats, key=order.index)

    def _win_uncontested(self) -> None:
        self._return_uncalled_bet()
        winner = next(p for p in self.players if p.live)
        amount = self.pot
        winner.stack += amount
        self.results = [PotResult(amount=amount, payouts={winner.seat: amount}, hand=None, label="the pot")]
        self._log("win", f"Everyone else folded. {winner.name} wins {amount} without showing their cards.",
                  seat=winner.seat, amount=amount)
        self._finish_hand()

    def _showdown(self) -> None:
        self.street = Street.SHOWDOWN
        live = [p for p in self.players if p.live]
        for p in self._ordered(live):
            value = evaluate(p.hole_cards + self.board)
            self.showdown_hands[p.seat] = value
            shown = " ".join(c.symbol for c in p.hole_cards)
            self._log("show", f"{p.name} shows {shown}: {value.describe()}.", seat=p.seat, cards=tuple(p.hole_cards))

        pots = build_pots(
            {p.seat: p.contributed for p in self.players if p.in_hand},
            folded={p.seat for p in self.players if p.folded},
        )
        for i, pot in enumerate(pots):
            label = "the pot" if len(pots) == 1 else ("the main pot" if i == 0 else f"side pot {i}")
            best = max(self.showdown_hands[s] for s in pot.eligible)
            winners = self._winners_in_button_order([s for s in pot.eligible if self.showdown_hands[s] == best])
            payouts = split_pot(pot.amount, winners)
            for seat, chips in payouts.items():
                self.players[seat].stack += chips
            self.results.append(PotResult(amount=pot.amount, payouts=payouts, hand=best.describe(), label=label))
            names = " and ".join(self.players[s].name for s in winners)
            if len(winners) == 1:
                text = f"{names} wins {label} ({pot.amount}) with {best.describe()}."
            else:
                text = f"{names} split {label} ({pot.amount}) with {best.describe()}."
            self._log("win", text, seat=winners[0], amount=pot.amount)
        self._finish_hand()

    def _ordered(self, players: Sequence[Player]) -> list[Player]:
        order = self.seats_after(self.button)
        return sorted(players, key=lambda p: order.index(p.seat))

    def _finish_hand(self) -> None:
        self.in_progress = False
        self.to_act = None
        for p in self.players:
            if p.in_hand and p.stack == 0:
                self._log("bust", f"{p.name} is out of chips.", seat=p.seat)
