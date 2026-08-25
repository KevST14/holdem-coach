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


def test_minimum_raise_is_the_size_of_the_last_raise():
    g = three_handed()
    g.start_hand()
    g.act(A.RAISE, 30)  # raises by 20
    legal = g.legal_actions()
    assert (legal.to_call, legal.min_raise_to, legal.max_raise_to) == (25, 50, 1000)
    with pytest.raises(IllegalActionError):
        g.act(A.RAISE, 40)
    g.act(A.RAISE, 50)
    assert g.current_bet == 50
    assert g.legal_actions().min_raise_to == 70


def test_short_all_in_raise_does_not_reopen_betting():
    g = three_handed(stacks=(1000, 1000, 45))
    g.start_hand()
    g.act(A.RAISE, 30)  # Ann
    g.act(A.CALL)  # Bob
    legal = g.legal_actions()  # Cat can only go all-in for 45, short of a full raise to 50
    assert (legal.min_raise_to, legal.max_raise_to) == (45, 45)
    g.act(A.RAISE, 45)
    assert g.players[2].all_in
    legal = g.legal_actions()
    assert legal.seat == 0 and legal.to_call == 15 and not legal.can_raise
    g.act(A.CALL)
    assert not g.legal_actions().can_raise
    g.act(A.CALL)
    assert g.street is Street.FLOP


def test_side_pots_are_paid_to_the_right_players():
    g = three_handed(stacks=(100, 300, 1000))
    g.start_hand(rigged_deck(g, {0: "As Ah", 1: "Ks Kh", 2: "Qs Qh"}, board="2c 7d 9h Jc 3s"))
    g.act(A.RAISE, 100)
    g.act(A.RAISE, 300)
    g.act(A.CALL)
    assert not g.in_progress and g.street is Street.SHOWDOWN
    assert len(g.board) == 5
    assert [p.stack for p in g.players] == [300, 400, 700]
    assert [(r.label, r.amount) for r in g.results] == [("the main pot", 300), ("side pot 1", 400)]


def test_split_pot_gives_odd_chip_to_first_winner_left_of_button():
    g = three_handed()
    g.start_hand(rigged_deck(g, {0: "2c 3d", 1: "4c 5d", 2: "2d 3c"}, board="Ah Kh Qh Jh Th"))
    g.act(A.CALL)
    g.act(A.FOLD)
    g.act(A.CHECK)
    for _ in range(3):
        g.act(A.CHECK)
        g.act(A.CHECK)
    assert not g.in_progress
    assert g.results[0].amount == 25
    assert g.results[0].payouts == {2: 13, 0: 12}
    assert [p.stack for p in g.players] == [1002, 995, 1003]


def test_all_in_for_more_than_caller_has_gets_excess_back():
    g = heads_up(stacks=(500, 200))
    g.start_hand()
    g.act(A.RAISE, 500)
    assert g.legal_actions().to_call == 190
    g.act(A.CALL)
    assert not g.in_progress
    assert any(e.kind == "uncalled" and e.amount == 300 for e in g.events)
    assert total_chips(g) == 700
    assert g.players[0].stack >= 300


def test_big_blind_short_all_in():
    g = heads_up(stacks=(1000, 5))
    g.start_hand()
    assert g.players[1].all_in
    legal = g.legal_actions()
    assert legal.to_call == 5 and not legal.can_raise
    g.act(A.CALL)
    assert not g.in_progress and len(g.board) == 5
    assert total_chips(g) == 1005


def test_illegal_actions_are_rejected():
    g = heads_up()
    g.start_hand()
    with pytest.raises(IllegalActionError):
        g.act(A.CHECK)  # facing the big blind
    with pytest.raises(IllegalActionError):
        g.act(A.BET, 20)  # there is already a bet: it's a raise
    g.act(A.CALL)
    with pytest.raises(IllegalActionError):
        g.act(A.FOLD)  # big blind can check for free
    with pytest.raises(IllegalActionError):
        g.act(A.RAISE, 15)  # below the minimum
    g.act(A.CHECK)
    with pytest.raises(IllegalActionError):
        g.act(A.RAISE, 20)  # no bet yet on the flop: it's a bet
    with pytest.raises(IllegalActionError):
        g.start_hand()  # hand still running


def test_button_moves_and_busted_players_sit_out():
    g = three_handed(stacks=(100, 1000, 1000))
    g.start_hand(rigged_deck(g, {0: "7c 2d", 1: "As Ah"}, board="Kc Qd 9h 4s 3c"))
    g.act(A.RAISE, 100)
    g.act(A.CALL)
    g.act(A.FOLD)
    assert g.players[0].stack == 0
    assert g.events[-1].kind == "bust"

    g.start_hand()
    assert not g.players[0].in_hand
    assert g.button == 1
    assert (g.sb_seat, g.bb_seat) == (1, 2)  # heads-up now: the dealer posts the small blind


def test_game_over_when_one_player_has_all_the_chips():
    g = heads_up(stacks=(100, 100))
    g.start_hand(rigged_deck(g, {0: "As Ah", 1: "7c 2d"}, board="Kc Qd 9h 4s 3c"))
    g.act(A.RAISE, 100)
    g.act(A.CALL)
    assert g.is_over
    with pytest.raises(IllegalActionError):
        g.start_hand()


@pytest.mark.parametrize("seed", range(20))
def test_random_play_keeps_chips_and_finishes_hands(seed):
    rng = random.Random(seed)
    stacks = [rng.choice([50, 200, 1000, 3000]) for _ in range(rng.randint(2, 6))]
    g = Game([(f"P{i}", s) for i, s in enumerate(stacks)], small_blind=5, big_blind=10, rng=rng)
    total = sum(stacks)
    for _ in range(40):
        if g.is_over:
            break
        g.start_hand()
        for _ in range(500):
            if not g.in_progress:
                break
            legal = g.legal_actions()
            options = []
            if legal.can_fold:
                options.append((A.FOLD, None))
            if legal.can_check:
                options.append((A.CHECK, None))
            if legal.can_call:
                options.append((A.CALL, None))
            if legal.can_bet or legal.can_raise:
                kind = A.BET if legal.can_bet else A.RAISE
                options.append((kind, rng.randint(legal.min_raise_to, legal.max_raise_to)))
                options.append((kind, legal.max_raise_to))
            g.act(*rng.choice(options))
            assert total_chips(g) == total
        assert not g.in_progress
        assert sum(p.stack for p in g.players) == total
        assert all(p.stack >= 0 for p in g.players)
