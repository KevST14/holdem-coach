import random

import pytest

from conftest import total_chips
from holdem.bots import PERSONALITIES, Bot
from holdem.cards import parse_cards
from holdem.equity import estimate_equity
from holdem.game import Game


def test_aces_beat_a_random_hand_about_85_percent():
    eq = estimate_equity(parse_cards("As Ah"), opponents=1, iterations=3000, rng=random.Random(1))
    assert 0.82 < eq.share < 0.88


def test_more_opponents_lower_your_chances():
    hole = parse_cards("Ks Qs")
    rng = random.Random(2)
    one = estimate_equity(hole, opponents=1, iterations=1500, rng=rng).share
    four = estimate_equity(hole, opponents=4, iterations=1500, rng=rng).share
    assert four < one


def test_made_nuts_on_river_always_wins():
    eq = estimate_equity(parse_cards("As Ks"), parse_cards("Qs Js Ts 2c 3d"), opponents=3, iterations=200)
    assert eq.win == 1.0 and eq.share == 1.0


def test_board_royal_flush_always_splits():
    eq = estimate_equity(parse_cards("2c 3d"), parse_cards("Ah Kh Qh Jh Th"), opponents=1, iterations=200)
    assert eq.tie == 1.0 and eq.share == pytest.approx(0.5)


def test_equity_rejects_bad_input():
    with pytest.raises(ValueError):
        estimate_equity(parse_cards("As"))
    with pytest.raises(ValueError):
        estimate_equity(parse_cards("As Ah"), opponents=0)


@pytest.mark.parametrize("seed", range(5))
def test_bots_play_whole_games_legally(seed):
    rng = random.Random(seed)
    names = [p.name for p in PERSONALITIES]
    g = Game([(n, 500, True) for n in names], small_blind=5, big_blind=10, rng=rng)
    bots = {i: Bot(p, rng=rng, iterations=40) for i, p in enumerate(PERSONALITIES)}
    for _ in range(15):
        if g.is_over:
            break
        g.start_hand()
        while g.in_progress:
            decision = bots[g.to_act].decide(g)
            g.act(decision.action, decision.amount)
            assert total_chips(g) == 2500
    assert sum(p.stack for p in g.players) == 2500


def test_bot_with_the_nuts_never_folds():
    g = Game([("Bot", 1000, True), ("You", 1000)], small_blind=5, big_blind=10, button=0)
    from conftest import rigged_deck
    g.start_hand(rigged_deck(g, {0: "As Ah", 1: "7c 2d"}, board="Ac Ad 9h 4s 3c"))
    bot = Bot(PERSONALITIES[1], rng=random.Random(0), iterations=100)
    for _ in range(20):
        assert bot.decide(g).action != "fold"
