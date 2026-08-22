import random

import pytest

from conftest import rigged_deck, total_chips
from holdem.game import ActionType as A
from holdem.game import Game, IllegalActionError, Street


def heads_up(stacks=(1000, 1000)):
    return Game([("Ann", stacks[0]), ("Bob", stacks[1])], small_blind=5, big_blind=10, button=0)


def three_handed(stacks=(1000, 1000, 1000)):
    return Game([("Ann", stacks[0]), ("Bob", stacks[1]), ("Cat", stacks[2])], small_blind=5, big_blind=10, button=0)


def test_heads_up_dealer_posts_small_blind_and_acts_first_preflop_only():
    g = heads_up()
    g.start_hand()
    assert (g.sb_seat, g.bb_seat) == (0, 1)
    assert [p.stack for p in g.players] == [995, 990]
    assert g.to_act == 0
    g.act(A.CALL)
    assert g.to_act == 1  # big blind gets the option
    g.act(A.CHECK)
    assert g.street is Street.FLOP and len(g.board) == 3
    assert g.to_act == 1  # after the flop the dealer acts last


def test_big_blind_gets_option_when_everyone_calls():
    g = three_handed()
    g.start_hand()
    assert (g.sb_seat, g.bb_seat, g.to_act) == (1, 2, 0)
    g.act(A.CALL)
    g.act(A.CALL)
    assert g.to_act == 2
    legal = g.legal_actions()
    assert legal.can_check and legal.can_raise and not legal.can_fold
    g.act(A.CHECK)
    assert g.street is Street.FLOP
    assert g.to_act == 1  # first player left of the button
    assert g.pot == 30


def test_everyone_folds_and_uncalled_bet_goes_back():
    g = heads_up()
    g.start_hand()
    g.act(A.RAISE, 30)
    g.act(A.FOLD)
    assert not g.in_progress
    assert [p.stack for p in g.players] == [1010, 990]
    assert [e.kind for e in g.events][-2:] == ["uncalled", "win"]
    assert g.results[0].hand is None
