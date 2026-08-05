import random

import pytest

from holdem.cards import Card, Deck, parse_cards


def test_parse_and_format():
    card = Card.parse("As")
    assert card == Card(14, "s")
    assert str(card) == "As"
    assert card.name == "Ace of Spades"
    assert card.symbol == "A♠"
    assert str(Card.parse("td")) == "Td"


def test_parse_cards_with_or_without_spaces():
    assert parse_cards("As Kd") == parse_cards("AsKd") == [Card(14, "s"), Card(13, "d")]


@pytest.mark.parametrize("bad", ["", "A", "1s", "Ax", "10s"])
def test_parse_rejects_bad_cards(bad):
    with pytest.raises(ValueError):
        Card.parse(bad)


def test_deck_has_52_unique_cards_and_deals_from_top():
    deck = Deck(rng=random.Random(1))
    cards = deck.deal(52)
    assert len(set(cards)) == 52
    assert len(deck) == 0
    with pytest.raises(ValueError):
        deck.deal()


def test_seeded_decks_shuffle_the_same_way():
    assert Deck(rng=random.Random(7)).deal(5) == Deck(rng=random.Random(7)).deal(5)


def test_stacked_deck_keeps_order_and_rejects_duplicates():
    deck = Deck(parse_cards("As Kd Qh"))
    assert deck.deal(2) == parse_cards("As Kd")
    with pytest.raises(ValueError):
        Deck(parse_cards("As As"))


def test_remove_known_cards():
    deck = Deck(rng=random.Random(3))
    deck.remove(parse_cards("As Kd"))
    assert len(deck) == 50
    assert Card.parse("As") not in deck.deal(50)
