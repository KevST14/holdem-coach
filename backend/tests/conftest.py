from __future__ import annotations

from holdem.cards import Deck, full_deck, parse_cards
from holdem.game import Game


def rigged_deck(game: Game, holes: dict[int, str], board: str = "") -> Deck:
    """Build a deck so the next hand deals ``holes`` to seats and ``board`` to the table.

    Unspecified cards (other players' hands, burn cards) are filled from what's left.
    """
    in_hand = [p.seat for p in game.players if p.stack > 0]
    if game.hand_number == 0 and game.button in in_hand:
        button = game.button
    else:
        button = next(s for s in game.seats_after(game.button) if s in in_hand)
    deal_order = [s for s in game.seats_after(button) if s in in_hand]

    wanted = {seat: parse_cards(text) for seat, text in holes.items()}
    board_cards = parse_cards(board)
    used = {c for cards in wanted.values() for c in cards} | set(board_cards)
    spare = iter(c for c in full_deck() if c not in used)

    order = []
    for seat in deal_order:
        order += wanted.get(seat) or [next(spare), next(spare)]
    runout = board_cards + [next(spare) for _ in range(5 - len(board_cards))]
    order += [next(spare), *runout[:3], next(spare), runout[3], next(spare), runout[4]]
    order += list(spare)
    return Deck(order)


def total_chips(game: Game) -> int:
    return sum(p.stack for p in game.players) + game.pot * game.in_progress
