import pytest
from fastapi.testclient import TestClient

from holdem.api.app import app

client = TestClient(app)


def new_game(**overrides):
    body = {"player_name": "Kim", "bots": 3, "seed": 11, **overrides}
    res = client.post("/api/games", json=body)
    assert res.status_code == 200, res.text
    return res.json()


def play_simple(state):
    """Check or call whenever it's our turn until the hand ends."""
    for _ in range(50):
        if not state["in_progress"]:
            return state
        legal = state["legal"]
        action = "check" if legal["can_check"] else "call"
        res = client.post(f"/api/games/{state['id']}/actions", json={"action": action})
        assert res.status_code == 200, res.text
        state = res.json()
    raise AssertionError("hand never finished")


def test_new_game_deals_you_in_and_hides_bot_cards():
    state = new_game()
    assert state["hand_number"] == 1
    assert len(state["players"]) == 4
    you = state["players"][state["your_seat"]]
    assert you["is_you"] and len(you["cards"]) == 2
    others = [p for p in state["players"] if not p["is_you"]]
    assert all(p["style"] for p in others)
    if state["in_progress"]:
        assert all(p["cards"] is None for p in others)
    assert sum(p["stack"] for p in state["players"]) + (state["pot"] if state["in_progress"] else 0) == 4000


def test_coach_and_legal_actions_on_your_turn():
    state = new_game()
    for _ in range(20):
        if state["your_turn"]:
            break
        state = client.post(f"/api/games/{state['id']}/next-hand").json()
    assert state["your_turn"]
    coach = state["coach"]
    assert 0 <= coach["win_chance"] <= 1
    assert coach["suggestion"] in {"fold", "check", "call", "bet", "raise"}
    assert coach["actions"] and coach["reasoning"]
    assert state["legal"]["max_raise_to"] > 0


def test_play_several_hands():
    state = new_game()
    for _ in range(5):
        state = play_simple(state)
        assert state["results"]
        assert any(e["kind"] == "win" for e in state["events"])
        if state["game_over"]:
            break
        state = client.post(f"/api/games/{state['id']}/next-hand").json()


def test_errors():
    assert client.get("/api/games/nope").status_code == 404
    state = new_game()
    finished = play_simple(state)
    res = client.post(f"/api/games/{finished['id']}/actions", json={"action": "check"})
    assert res.status_code == 409
    if not finished["game_over"]:
        state = client.post(f"/api/games/{finished['id']}/next-hand").json()
        if state["your_turn"]:
            res = client.post(f"/api/games/{state['id']}/actions", json={"action": "raise", "amount": 1})
            assert res.status_code == 400
            assert client.post(f"/api/games/{state['id']}/next-hand").status_code == 409


@pytest.mark.parametrize("body", [{"bots": 0}, {"bots": 6}, {"small_blind": 20, "big_blind": 10}, {"starting_stack": 50}])
def test_rejects_bad_settings(body):
    assert client.post("/api/games", json=body).status_code == 422


def test_learn_content():
    data = client.get("/api/learn").json()
    assert data["rankings"][0]["name"] == "Royal Flush"
    assert len(data["rankings"]) == 10
    assert data["steps"] and data["glossary"]
