// Types mirror backend/src/holdem/api/schemas.py.

export type ActionType = "fold" | "check" | "call" | "bet" | "raise";

export interface Player {
  seat: number;
  name: string;
  stack: number;
  bet: number;
  in_hand: boolean;
  folded: boolean;
  all_in: boolean;
  is_you: boolean;
  is_button: boolean;
  is_small_blind: boolean;
  is_big_blind: boolean;
  cards: string[] | null;
  showdown_hand: string | null;
  style: string | null;
}

export interface GameEvent {
  kind: string;
  text: string;
  seat: number | null;
  action: ActionType | null;
  amount: number | null;
  street: string | null;
  cards: string[];
}

export interface PotResult {
  label: string;
  amount: number;
  hand: string | null;
  payouts: { seat: number; amount: number }[];
}

export interface Legal {
  can_fold: boolean;
  can_check: boolean;
  to_call: number;
  can_bet: boolean;
  can_raise: boolean;
  min_raise_to: number;
  max_raise_to: number;
}

export interface Coach {
  hand_name: string;
  hand_tip: string;
  draws: string[];
  win_chance: number;
  opponents: number;
  price: number | null;
  suggestion: ActionType;
  reasoning: string;
  actions: { action: ActionType; label: string; explanation: string }[];
}

export interface GameState {
  id: string;
  hand_number: number;
  street: string;
  in_progress: boolean;
  board: string[];
  pot: number;
  current_bet: number;
  small_blind: number;
  big_blind: number;
  to_act: number | null;
  your_seat: number;
  your_turn: boolean;
  your_hand: string | null;
  legal: Legal | null;
  coach: Coach | null;
  players: Player[];
  events: GameEvent[];
  results: PotResult[];
  game_over: boolean;
}

export interface NewGameSettings {
  player_name: string;
  bots: number;
  starting_stack: number;
  small_blind: number;
  big_blind: number;
}

export interface LearnContent {
  rankings: { name: string; example: string[]; example_description: string; explanation: string; odds: string }[];
  steps: { title: string; body: string }[];
  glossary: { term: string; definition: string }[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // keep the status text
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  newGame: (settings: NewGameSettings) =>
    request<GameState>("/api/games", { method: "POST", body: JSON.stringify(settings) }),
  act: (id: string, action: ActionType, amount?: number) =>
    request<GameState>(`/api/games/${id}/actions`, {
      method: "POST",
      body: JSON.stringify({ action, amount }),
    }),
  nextHand: (id: string) => request<GameState>(`/api/games/${id}/next-hand`, { method: "POST" }),
  learn: () => request<LearnContent>("/api/learn"),
};
