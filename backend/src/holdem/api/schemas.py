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
