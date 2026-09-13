import random

import pytest

from conftest import rigged_deck
from holdem.cards import parse_cards
from holdem.coach import chen_score, coach, describe_hand, find_draws, starting_hand_name
from holdem.evaluator import evaluate
from holdem.game import ActionType, Game
from holdem.learn import HAND_RANKINGS


@pytest.mark.parametrize(
    "hole, name, score",
    [
        ("As Ah", "Pocket Aces", 20),
        ("Ks Kd", "Pocket Kings", 16),
        ("2c 2d", "Pocket Twos", 5),
        ("As Ks", "Ace-King suited", 12),
        ("Kd Ac", "Ace-King offsuit", 10),
        ("7c 2d", "Seven-Two offsuit", -1),
        ("Ts 9s", "Ten-Nine suited", 8),
    ],
)
def test_starting_hands(hole, name, score):
    assert starting_hand_name(parse_cards(hole)) == name
    assert chen_score(parse_cards(hole)) == score


def test_describe_preflop_and_postflop():
    assert describe_hand(parse_cards("As Ah"), []).tip.startswith("One of the best")
    assert describe_hand(parse_cards("7c 2d"), []).tip.startswith("A weak")
    top_pair = describe_hand(parse_cards("Kc 9d"), parse_cards("Kh 7s 2c"))
    assert top_pair.name == "Pair of Kings" and top_pair.tip.startswith("Top pair")
    overpair = describe_hand(parse_cards("Qc Qd"), parse_cards("Jh 7s 2c"))
    assert overpair.tip.startswith("An overpair")
    on_board = describe_hand(parse_cards("2c 3d"), parse_cards("Ah Kh Qh Jh Th"))
    assert "all on the board" in on_board.tip


def test_draws():
    flush = find_draws(parse_cards("Ah 5h"), parse_cards("Kh 9h 2c"))
    assert any(d.startswith("Flush draw: one more heart") and "36%" in d for d in flush)
    open_ended = find_draws(parse_cards("9c 8d"), parse_cards("7h 6s Kc"))
    assert any(d.startswith("Open-ended") for d in open_ended)
    gutshot = find_draws(parse_cards("9c 8d"), parse_cards("6h 5s Kc 2d"))
    assert any(d.startswith("Gutshot") and "8%" in d for d in gutshot)
    assert find_draws(parse_cards("Ac Kd"), parse_cards("7h 2s 9c")) == []
    assert find_draws(parse_cards("9h 8h"), parse_cards("7h 6h 5h")) == []  # already made


def test_coach_suggests_folding_trash_to_a_big_bet():
    g = Game([("You", 1000), ("Bot", 1000)], small_blind=5, big_blind=10, button=1)
    g.start_hand(rigged_deck(g, {0: "7c 2d", 1: "As Ah"}, board="Ac Kd Qh 4s 3c"))
    g.act(ActionType.CALL)  # Bot (dealer) limps
    g.act(ActionType.CHECK)  # You
    g.act(ActionType.CHECK)  # You, first to act on the flop
    g.act(ActionType.BET, 200)  # Bot
    assert g.to_act == 0
    advice = coach(g, iterations=300, rng=random.Random(0))
    assert advice.suggestion is ActionType.FOLD
    assert advice.price is not None and "need to win at least" in advice.reasoning


def test_coach_suggests_betting_the_nuts():
    g = Game([("You", 1000), ("Bot", 1000)], small_blind=5, big_blind=10, button=1)
    g.start_hand(rigged_deck(g, {0: "As Ah", 1: "7c 2d"}, board="Ac Ad 9h 4s 3c"))
    g.act(ActionType.CALL)
    g.act(ActionType.CHECK)
    assert g.to_act == 0
    advice = coach(g, iterations=200, rng=random.Random(0))
    assert advice.suggestion is ActionType.BET
    assert advice.hand.name == "Four of a Kind, Aces"
    assert [h.action for h in advice.actions] == [ActionType.CHECK, ActionType.BET]


def test_ranking_examples_match_their_names():
    for lesson in HAND_RANKINGS:
        assert evaluate(lesson.example).name == lesson.name
