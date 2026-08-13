from holdem.pots import Pot, build_pots, split_pot


def test_single_pot_when_everyone_puts_in_the_same():
    assert build_pots({0: 100, 1: 100, 2: 100}, folded=set()) == [Pot(300, frozenset({0, 1, 2}))]


def test_short_all_in_creates_side_pot():
    pots = build_pots({0: 50, 1: 200, 2: 200}, folded=set())
    assert pots == [Pot(150, frozenset({0, 1, 2})), Pot(300, frozenset({1, 2}))]


def test_three_levels():
    pots = build_pots({0: 25, 1: 100, 2: 300, 3: 300}, folded=set())
    assert pots == [
        Pot(100, frozenset({0, 1, 2, 3})),
        Pot(225, frozenset({1, 2, 3})),
        Pot(400, frozenset({2, 3})),
    ]


def test_folded_chips_count_but_folder_cannot_win():
    pots = build_pots({0: 100, 1: 100, 2: 100}, folded={0})
    assert pots == [Pot(300, frozenset({1, 2}))]


def test_all_in_player_only_wins_what_they_matched():
    pots = build_pots({0: 100, 1: 40, 2: 100}, folded={0})
    assert pots == [Pot(120, frozenset({1, 2})), Pot(120, frozenset({2}))]


def test_folded_player_who_put_in_more_than_live_players():
    pots = build_pots({0: 30, 1: 80, 2: 50}, folded={1})
    assert pots == [Pot(90, frozenset({0, 2})), Pot(70, frozenset({2}))]
    assert sum(p.amount for p in pots) == 160


def test_split_gives_odd_chip_to_first_winner():
    assert split_pot(101, [3, 1]) == {3: 51, 1: 50}
    assert split_pot(100, [2]) == {2: 100}
    assert split_pot(10, [0, 1, 2]) == {0: 4, 1: 3, 2: 3}
