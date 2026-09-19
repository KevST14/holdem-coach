"""Request and response models, plus the conversion from engine state."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from holdem.api.sessions import Session
from holdem.coach import Coaching, coach, describe_hand
from holdem.game import ActionType
from holdem.learn import GLOSSARY, HAND_RANKINGS, HOW_A_HAND_WORKS


class NewGameRequest(BaseModel):
    player_name: str = Field("Player", min_length=1, max_length=20)
    bots: int = Field(3, ge=1, le=5)
    starting_stack: int = Field(1000, ge=100, le=100_000)
    small_blind: int = Field(5, ge=1)
    big_blind: int = Field(10, ge=1)
    seed: int | None = None

    @model_validator(mode="after")
    def blinds_make_sense(self) -> NewGameRequest:
        if self.small_blind > self.big_blind:
            raise ValueError("small blind can't be bigger than the big blind")
        if self.big_blind * 10 > self.starting_stack:
            raise ValueError("starting stack should be at least 10 big blinds")
        return self


class ActionRequest(BaseModel):
    action: ActionType
    amount: int | None = None


class PlayerOut(BaseModel):
    seat: int
    name: str
    stack: int
    bet: int
    in_hand: bool
    folded: bool
    all_in: bool
    is_you: bool
    is_button: bool
    is_small_blind: bool
    is_big_blind: bool
    cards: list[str] | None  # None when hidden from you
    showdown_hand: str | None
    style: str | None  # bot personality


class EventOut(BaseModel):
    kind: str
    text: str
    seat: int | None
    action: ActionType | None
    amount: int | None
    street: str | None
    cards: list[str]


class PayoutOut(BaseModel):
    seat: int
    amount: int


class PotResultOut(BaseModel):
    label: str
    amount: int
    hand: str | None
    payouts: list[PayoutOut]


class ActionHelpOut(BaseModel):
    action: ActionType
    label: str
    explanation: str


class LegalOut(BaseModel):
    can_fold: bool
    can_check: bool
    to_call: int
    can_bet: bool
    can_raise: bool
    min_raise_to: int
    max_raise_to: int


class CoachOut(BaseModel):
    hand_name: str
    hand_tip: str
    draws: list[str]
    win_chance: float
    opponents: int
    price: float | None
    suggestion: ActionType
    reasoning: str
    actions: list[ActionHelpOut]


class GameState(BaseModel):
    id: str
    hand_number: int
    street: str
    in_progress: bool
    board: list[str]
    pot: int
    current_bet: int
    small_blind: int
    big_blind: int
    to_act: int | None
    your_seat: int
    your_turn: bool
    your_hand: str | None  # what your cards make right now
    legal: LegalOut | None
    coach: CoachOut | None
    players: list[PlayerOut]
    events: list[EventOut]
    results: list[PotResultOut]
    game_over: bool


def _coach_out(c: Coaching) -> CoachOut:
    return CoachOut(
        hand_name=c.hand.name,
        hand_tip=c.hand.tip,
        draws=c.hand.draws,
        win_chance=c.win_chance,
        opponents=c.opponents,
        price=c.price,
        suggestion=c.suggestion,
        reasoning=c.reasoning,
        actions=[ActionHelpOut(action=h.action, label=h.label, explanation=h.explanation) for h in c.actions],
    )


def game_state(session: Session) -> GameState:
    g = session.game
    you = g.players[session.human_seat]
    your_turn = g.in_progress and g.to_act == session.human_seat
    legal = g.legal_actions() if your_turn else None

    players = []
    for p in g.players:
        is_you = p.seat == session.human_seat
        shown = is_you or p.seat in g.showdown_hands
        bot = session.bots.get(p.seat)
        hand = g.showdown_hands.get(p.seat)
        players.append(PlayerOut(
            seat=p.seat,
            name=p.name,
            stack=p.stack,
            bet=p.bet,
            in_hand=p.in_hand,
            folded=p.folded,
            all_in=p.all_in,
            is_you=is_you,
            is_button=p.seat == g.button,
            is_small_blind=p.seat == g.sb_seat,
            is_big_blind=p.seat == g.bb_seat,
            cards=[str(c) for c in p.hole_cards] if shown and p.hole_cards else None,
            showdown_hand=hand.describe() if hand else None,
            style=bot.personality.style if bot else None,
        ))

    return GameState(
        id=session.id,
        hand_number=g.hand_number,
        street=g.street.value,
        in_progress=g.in_progress,
        board=[str(c) for c in g.board],
        pot=g.pot,
        current_bet=g.current_bet,
        small_blind=g.small_blind,
        big_blind=g.big_blind,
        to_act=g.to_act,
        your_seat=session.human_seat,
        your_turn=your_turn,
        your_hand=describe_hand(you.hole_cards, g.board).name if you.hole_cards else None,
        legal=LegalOut(**{k: getattr(legal, k) for k in LegalOut.model_fields}) if legal else None,
        coach=_coach_out(coach(g, rng=session.rng)) if your_turn else None,
        players=players,
        events=[
            EventOut(kind=e.kind, text=e.text, seat=e.seat, action=e.action, amount=e.amount,
                     street=e.street.value if e.street else None,
                     cards=[str(c) for c in e.cards])
            for e in g.events
        ],
        results=[
            PotResultOut(label=r.label, amount=r.amount, hand=r.hand,
                         payouts=[PayoutOut(seat=s, amount=a) for s, a in r.payouts.items()])
            for r in g.results
        ],
        game_over=g.is_over or (not g.in_progress and you.stack == 0),
    )


def learn_content() -> dict:
    return {
        "rankings": [
            {
                "name": r.name,
                "example": [str(c) for c in r.example],
                "example_description": r.example_description,
                "explanation": r.explanation,
                "odds": r.odds,
            }
            for r in HAND_RANKINGS
        ],
        "steps": [{"title": title, "body": body} for title, body in HOW_A_HAND_WORKS],
        "glossary": [{"term": term, "definition": d} for term, d in GLOSSARY.items()],
    }
