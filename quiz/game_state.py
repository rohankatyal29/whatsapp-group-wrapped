"""Data models for the quiz game state."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
import time
import random


class GamePhase(Enum):
    LOBBY = "lobby"
    QUESTION = "question"
    REVEAL = "reveal"
    FINISHED = "finished"


@dataclass
class Question:
    id: int
    text: str
    options: list[str]
    correct_index: int
    category: str
    points: int = 100


@dataclass
class Player:
    id: str
    name: str
    websocket: Any = None  # WebSocket connection
    score: int = 0
    current_answer: Optional[int] = None
    answer_time: Optional[float] = None
    connected: bool = True
    total_answer_time: float = 0.0
    answers_count: int = 0
    last_answer_time: Optional[float] = None
    last_answer_index: Optional[int] = None
    last_answer_correct: Optional[bool] = None
    last_answer_ts: Optional[float] = None
    last_answer_question_index: Optional[int] = None

    def reset_for_question(self):
        """Reset player state for a new question."""
        self.current_answer = None
        self.answer_time = None

    def to_dict(self) -> dict:
        avg_time = None
        if self.answers_count > 0:
            avg_time = self.total_answer_time / self.answers_count
        return {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "has_answered": self.current_answer is not None,
            "connected": self.connected,
            "avg_answer_time": avg_time,
            "last_answer_time": self.last_answer_time,
            "last_answer_index": self.last_answer_index,
            "last_answer_correct": self.last_answer_correct,
            "last_answer_ts": self.last_answer_ts,
            "last_answer_question_index": self.last_answer_question_index,
        }


@dataclass
class GameState:
    code: str
    phase: GamePhase = GamePhase.LOBBY
    players: dict[str, Player] = field(default_factory=dict)
    questions: list[Question] = field(default_factory=list)
    current_question_index: int = 0
    question_start_time: Optional[float] = None
    whatsapp_data: dict = field(default_factory=dict)

    def current_question(self) -> Optional[Question]:
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    def start_question(self):
        """Start timing for current question."""
        self.question_start_time = time.time()
        for player in self.players.values():
            player.reset_for_question()

    def all_answered(self) -> bool:
        """Check if all players have answered."""
        return all(p.current_answer is not None for p in self.players.values())

    def get_rankings(self) -> list[dict]:
        """Get current rankings sorted by score."""
        def avg_time(player: Player) -> float:
            if player.answers_count > 0:
                return player.total_answer_time / player.answers_count
            return float("inf")

        # Tie-breaker: higher score wins; if tied, faster average answer time wins.
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (-p.score, avg_time(p), p.name.casefold()),
        )
        return [
            {"rank": i + 1, "name": p.name, "score": p.score, "id": p.id}
            for i, p in enumerate(sorted_players)
        ]


def shuffle_question(question: Question) -> Question:
    """Return a new Question with randomized options and adjusted correct index."""
    indices = list(range(len(question.options)))
    random.shuffle(indices)
    shuffled_options = [question.options[i] for i in indices]
    new_correct_index = indices.index(question.correct_index)
    return Question(
        id=question.id,
        text=question.text,
        options=shuffled_options,
        correct_index=new_correct_index,
        category=question.category,
        points=question.points,
    )


# Sample questions for testing
SAMPLE_QUESTIONS = [
    Question(
        id=0,
        text="Who sent the most messages in the last year?",
        options=["Alice", "Bob", "Charlie", "David"],
        correct_index=2,
        category="message_count",
    ),
    Question(
        id=1,
        text="Who is the biggest night owl (texts 11PM-4AM)?",
        options=["Alice", "Bob", "Charlie", "David"],
        correct_index=0,
        category="late_night",
    ),
    Question(
        id=2,
        text="What is Bob's most-used emoji?",
        options=["😂", "❤️", "🔥", "👍"],
        correct_index=1,
        category="emoji",
    ),
    Question(
        id=3,
        text="Who has the fastest average reply time?",
        options=["Alice", "Bob", "Charlie", "David"],
        correct_index=3,
        category="reply_speed",
    ),
    Question(
        id=4,
        text="Who starts the most conversations each day?",
        options=["Alice", "Bob", "Charlie", "David"],
        correct_index=1,
        category="conversation_starter",
    ),
]
