import random
from itertools import combinations

import pytest

from holdem.cards import full_deck, parse_cards
from holdem.evaluator import HandCategory, evaluate


def ev(text):
    return evaluate(parse_cards(text))


@pytest.mark.parametrize(
    "cards, category, description",
    [
        ("Ah Kh Qh Jh Th 2c 3d", HandCategory.STRAIGHT_FLUSH, "Royal Flush"),
        ("9s 8s 7s 6s 5s Ad Ac", HandCategory.STRAIGHT_FLUSH, "Straight Flush, Nine high"),
        ("Ad 2d 3d 4d 5d Kc Ks", HandCategory.STRAIGHT_FLUSH, "Straight Flush, Five high"),
        ("7c 7d 7h 7s Kd 2c 3c", HandCategory.FOUR_OF_A_KIND, "Four of a Kind, Sevens"),
        ("Kc Kd Ks 7h 7s 2c 3d", HandCategory.FULL_HOUSE, "Full House, Kings full of Sevens"),
        ("Ac Jc 8c 4c 2c Kd Qh", HandCategory.FLUSH, "Flush, Ace high"),
        ("9c 8d 7h 6s 5c 2d 2h", HandCategory.STRAIGHT, "Straight, Nine high"),
        ("Ac 2d 3h 4s 5c 9d Jh", HandCategory.STRAIGHT, "Straight, Five high"),
        ("Qc Qd Qs 9h 4s 2c 7d", HandCategory.THREE_OF_A_KIND, "Three of a Kind, Queens"),
        ("Jc Jd 4h 4s Ac 9d 2h", HandCategory.TWO_PAIR, "Two Pair, Jacks and Fours"),
        ("6c 6d Ah Ks 9c 4d 2h", HandCategory.PAIR, "Pair of Sixes"),
        ("Ac Jd 9h 7s 4c 3d 2h", HandCategory.HIGH_CARD, "High Card, Ace"),
    ],
)
def test_categories_and_descriptions(cards, category, description):
    value = ev(cards)
    assert value.category is category
    assert value.describe() == description
    assert len(value.cards) == 5


def test_category_order():
    hands = [
        "Ac Jd 9h 7s 4c",
        "6c 6d Ah Ks 9c",
        "Jc Jd 4h 4s Ac",
        "Qc Qd Qs 9h 4s",
        "9c 8d 7h 6s 5c",
        "Ac Jc 8c 4c 2c",
        "Kc Kd Ks 7h 7s",
        "7c 7d 7h 7s Kd",
        "9s 8s 7s 6s 5s",
    ]
    values = [ev(h) for h in hands]
    assert values == sorted(values)


def test_kicker_decides_between_equal_pairs():
    board = "Kh 9d 5c 3s 2h"
    assert ev(f"Ks Qd {board}") > ev(f"Kc Jd {board}")


def test_board_plays_and_splits():
    board = "Ah Kh Qd Jc Ts"
    assert ev(f"2c 3d {board}") == ev(f"4s 5s {board}")


def test_wheel_loses_to_six_high_straight():
    assert ev("Ac 2d 3h 4s 5c") < ev("2d 3h 4s 5c 6d")


def test_two_trips_make_a_full_house():
    value = ev("Kc Kd Ks 7h 7s 7d 2c")
    assert value.describe() == "Full House, Kings full of Sevens"


def test_three_pairs_use_best_kicker():
    value = ev("Ac Ad Kc Kd 5h 5s Qc")
    assert value.category is HandCategory.TWO_PAIR
    assert value.tiebreak == (14, 13, 12)


def test_flush_uses_top_five_of_six_suited():
    value = ev("Ah 9h 7h 5h 3h 2h Kc")
    assert value.tiebreak == (14, 9, 7, 5, 3)


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        ev("Ac Kd Qh Js")
    with pytest.raises(ValueError):
        ev("Ac Ac Qh Js Td")
