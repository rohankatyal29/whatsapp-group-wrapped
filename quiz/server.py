"""FastAPI server for the WhatsApp Group Wrapped Quiz."""

import asyncio
import json
import random
import socket
import string
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .game_state import GamePhase, GameState, Player, Question, SAMPLE_QUESTIONS, shuffle_question
from .scoring import calculate_score

app = FastAPI(title="WhatsApp Group Wrapped Quiz")

# In-memory game storage
games: dict[str, GameState] = {}

# WebSocket connections (separate from Player objects for quiz master)
quiz_master_connections: dict[str, WebSocket] = {}

# Get the directory where this file is located
BASE_DIR = Path(__file__).parent

# Simple local persistence for answers/events
RESPONSES_PATH = BASE_DIR.parent / "responses.txt"
SCORES_PATH = BASE_DIR.parent / "scores.txt"
STATE_PATH = BASE_DIR.parent / "game_state.txt"
RESPONSES_LOCK = asyncio.Lock()
SCORES_LOCK = asyncio.Lock()
STATE_LOCK = asyncio.Lock()

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


async def append_json_line(path: Path, lock: asyncio.Lock, event: dict):
    """Append a JSON line event to a local text file."""
    payload = dict(event)
    payload.setdefault("ts", time.time())
    line = json.dumps(payload, ensure_ascii=True)
    async with lock:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
        except Exception:
            # Logging should never crash the game flow
            pass


async def append_event(event: dict):
    await append_json_line(RESPONSES_PATH, RESPONSES_LOCK, event)


async def append_score(event: dict):
    await append_json_line(SCORES_PATH, SCORES_LOCK, event)


def serialize_question(question: Question) -> dict:
    return {
        "id": question.id,
        "text": question.text,
        "options": list(question.options),
        "correct_index": question.correct_index,
        "category": question.category,
        "points": question.points,
    }


def serialize_player(player: Player) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "score": player.score,
        "current_answer": player.current_answer,
        "answer_time": player.answer_time,
        "connected": player.connected,
        "total_answer_time": player.total_answer_time,
        "answers_count": player.answers_count,
        "last_answer_time": player.last_answer_time,
        "last_answer_index": player.last_answer_index,
        "last_answer_correct": player.last_answer_correct,
        "last_answer_ts": player.last_answer_ts,
        "last_answer_question_index": player.last_answer_question_index,
    }


def serialize_game(game: GameState) -> dict:
    question_elapsed = None
    if game.question_start_time is not None:
        question_elapsed = max(0.0, time.time() - game.question_start_time)

    return {
        "code": game.code,
        "phase": game.phase.value,
        "current_question_index": game.current_question_index,
        "question_elapsed": question_elapsed,
        "questions": [serialize_question(q) for q in game.questions],
        "players": [serialize_player(p) for p in game.players.values()],
    }


async def save_state():
    payload = {
        "saved_at": time.time(),
        "games": {code: serialize_game(game) for code, game in games.items()},
    }
    data = json.dumps(payload, ensure_ascii=True)
    tmp_path = STATE_PATH.with_suffix(".tmp")
    async with STATE_LOCK:
        try:
            tmp_path.write_text(data, encoding="utf-8")
            tmp_path.replace(STATE_PATH)
        except Exception:
            pass


def load_state():
    if not STATE_PATH.exists():
        return
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return

    restored_games: dict[str, GameState] = {}
    for game_code, game_data in (data.get("games") or {}).items():
        try:
            game = GameState(
                code=game_code,
                phase=GamePhase(game_data.get("phase", GamePhase.LOBBY.value)),
            )
            game.current_question_index = int(game_data.get("current_question_index", 0))
            question_elapsed = game_data.get("question_elapsed")
            if question_elapsed is not None:
                game.question_start_time = time.time() - float(question_elapsed)

            game.questions = [
                Question(
                    id=q["id"],
                    text=q["text"],
                    options=list(q["options"]),
                    correct_index=q["correct_index"],
                    category=q.get("category", ""),
                    points=q.get("points", 100),
                )
                for q in game_data.get("questions", [])
            ]

            game.players = {}
            for pdata in game_data.get("players", []):
                player = Player(
                    id=pdata["id"],
                    name=pdata["name"],
                    websocket=None,
                    score=pdata.get("score", 0),
                    current_answer=pdata.get("current_answer"),
                    answer_time=pdata.get("answer_time"),
                    connected=False,
                    total_answer_time=pdata.get("total_answer_time", 0.0),
                    answers_count=pdata.get("answers_count", 0),
                    last_answer_time=pdata.get("last_answer_time"),
                    last_answer_index=pdata.get("last_answer_index"),
                    last_answer_correct=pdata.get("last_answer_correct"),
                    last_answer_ts=pdata.get("last_answer_ts"),
                    last_answer_question_index=pdata.get("last_answer_question_index"),
                )
                game.players[player.id] = player

            restored_games[game_code] = game
        except Exception:
            continue

    if restored_games:
        games.clear()
        games.update(restored_games)


@app.on_event("startup")
async def startup_load_state():
    load_state()


def build_question_payload(game: GameState) -> dict | None:
    question = game.current_question()
    if not question:
        return None
    answered_count = sum(1 for p in game.players.values() if p.current_answer is not None)
    total_players = len(game.players)
    return {
        "type": "question",
        "question_index": game.current_question_index,
        "question_number": game.current_question_index + 1,
        "total_questions": len(game.questions),
        "text": question.text,
        "options": question.options,
        "answered_count": answered_count,
        "total_players": total_players,
        "remaining_count": max(0, total_players - answered_count),
    }


def build_reveal_payload(game: GameState) -> dict | None:
    question = game.current_question()
    if not question:
        return None

    player_results = []
    for player in game.players.values():
        is_correct = player.current_answer == question.correct_index
        points_earned = 0
        if is_correct and player.answer_time is not None:
            points_earned = calculate_score(True, player.answer_time)

        player_results.append({
            "player_id": player.id,
            "name": player.name,
            "answer": player.current_answer,
            "correct": is_correct,
            "points_earned": points_earned,
            "total_score": player.score,
        })

    return {
        "type": "reveal",
        "correct_index": question.correct_index,
        "correct_answer": question.options[question.correct_index],
        "player_results": player_results,
        "rankings": game.get_rankings(),
    }


def build_game_over_payload(game: GameState) -> dict:
    rankings = game.get_rankings()
    winner = rankings[0]["name"] if rankings else "No one"
    return {
        "type": "game_over",
        "winner": winner,
        "final_rankings": rankings,
    }


async def send_current_state_to_player(websocket: WebSocket, game: GameState, player: Player):
    """Send the current game state to a (re)connected player."""
    if game.phase == GamePhase.QUESTION:
        payload = build_question_payload(game)
        if payload:
            await websocket.send_json(payload)
            if player.current_answer is not None:
                await websocket.send_json({
                    "type": "answer_confirmed",
                    "answer_index": player.current_answer,
                })
            answered_count = sum(
                1 for p in game.players.values() if p.current_answer is not None
            )
            total_players = len(game.players)
            await websocket.send_json({
                "type": "answer_progress",
                "answered_count": answered_count,
                "total_players": total_players,
                "remaining_count": max(0, total_players - answered_count),
            })
    elif game.phase == GamePhase.REVEAL:
        payload = build_reveal_payload(game)
        if payload:
            await websocket.send_json(payload)
    elif game.phase == GamePhase.FINISHED:
        await websocket.send_json(build_game_over_payload(game))


def get_local_ip() -> str:
    """Get the local IP address for LAN access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def generate_game_code() -> str:
    """Generate a 4-letter game code."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4))
        if code not in games:
            return code


@app.get("/", response_class=HTMLResponse)
async def quiz_master_page():
    """Serve the quiz master dashboard."""
    html_path = BASE_DIR / "templates" / "master.html"
    return HTMLResponse(html_path.read_text())


@app.get("/play", response_class=HTMLResponse)
async def player_page():
    """Serve the player join/play page."""
    html_path = BASE_DIR / "templates" / "player.html"
    return HTMLResponse(html_path.read_text())


@app.post("/api/create-game")
async def create_game():
    """Create a new game with sample questions."""
    game_code = generate_game_code()

    game = GameState(
        code=game_code,
        questions=[shuffle_question(q) for q in SAMPLE_QUESTIONS],
    )
    games[game_code] = game

    await append_event({
        "event": "game_created",
        "game_code": game_code,
        "question_count": len(game.questions),
    })
    await save_state()

    return {
        "code": game_code,
        "question_count": len(game.questions),
        "local_ip": get_local_ip(),
    }


@app.get("/api/game/{game_code}")
async def get_game_info(game_code: str):
    """Get info about a game."""
    game = games.get(game_code.upper())
    if not game:
        return {"error": "Game not found"}

    return {
        "code": game.code,
        "phase": game.phase.value,
        "player_count": len(game.players),
        "question_count": len(game.questions),
    }


async def broadcast_to_players(game: GameState, message: dict):
    """Send a message to all players in a game."""
    for player in game.players.values():
        if not player.connected or not player.websocket:
            continue
        try:
            await player.websocket.send_json(message)
        except Exception:
            player.connected = False
            player.websocket = None


async def broadcast_to_quiz_master(game: GameState, message: dict):
    """Send a message to the quiz master."""
    ws = quiz_master_connections.get(game.code)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            pass


async def broadcast_player_list(game: GameState):
    """Broadcast updated player list to everyone."""
    message = {
        "type": "player_list",
        "players": [p.to_dict() for p in game.players.values()],
    }
    await broadcast_to_players(game, message)
    await broadcast_to_quiz_master(game, message)


async def broadcast_question(game: GameState):
    """Broadcast current question to all players."""
    message = build_question_payload(game)
    if not message:
        return
    await broadcast_to_players(game, message)
    await broadcast_to_quiz_master(game, message)


async def broadcast_reveal(game: GameState):
    """Broadcast answer reveal to all players."""
    message = build_reveal_payload(game)
    if not message:
        return
    await broadcast_to_players(game, message)
    await broadcast_to_quiz_master(game, message)


async def broadcast_game_over(game: GameState):
    """Broadcast game over to all players."""
    message = build_game_over_payload(game)
    await broadcast_to_players(game, message)
    await broadcast_to_quiz_master(game, message)


@app.websocket("/ws/master/{game_code}")
async def quiz_master_websocket(websocket: WebSocket, game_code: str):
    """WebSocket endpoint for quiz master."""
    await websocket.accept()

    game_code = game_code.upper()
    game = games.get(game_code)
    if not game:
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close(code=4004)
        return

    quiz_master_connections[game_code] = websocket

    # Send initial state
    await websocket.send_json({
        "type": "game_state",
        "code": game.code,
        "phase": game.phase.value,
        "players": [p.to_dict() for p in game.players.values()],
        "question_count": len(game.questions),
        "current_question_index": game.current_question_index,
        "local_ip": get_local_ip(),
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "start_game":
                if game.phase == GamePhase.LOBBY and any(
                    p.connected for p in game.players.values()
                ):
                    game.phase = GamePhase.QUESTION
                    game.current_question_index = 0
                    game.start_question()
                    await append_event({
                        "event": "game_started",
                        "game_code": game.code,
                    })
                    await save_state()
                    await broadcast_question(game)
                elif not game.players:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Need at least one player to start"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Need at least one connected player to start"
                    })

            elif msg_type == "reveal_answer":
                if game.phase == GamePhase.QUESTION:
                    game.phase = GamePhase.REVEAL
                    await append_event({
                        "event": "answer_reveal",
                        "game_code": game.code,
                        "question_index": game.current_question_index,
                    })
                    await save_state()
                    await broadcast_reveal(game)

            elif msg_type == "next_question":
                if game.phase == GamePhase.REVEAL:
                    game.current_question_index += 1
                    if game.current_question_index >= len(game.questions):
                        game.phase = GamePhase.FINISHED
                        await append_event({
                            "event": "game_finished",
                            "game_code": game.code,
                        })
                        await save_state()
                        await broadcast_game_over(game)
                    else:
                        game.phase = GamePhase.QUESTION
                        game.start_question()
                        await append_event({
                            "event": "question_started",
                            "game_code": game.code,
                            "question_index": game.current_question_index,
                        })
                        await save_state()
                        await broadcast_question(game)

    except WebSocketDisconnect:
        if game_code in quiz_master_connections:
            del quiz_master_connections[game_code]


@app.websocket("/ws/player/{game_code}/{player_name}")
async def player_websocket(websocket: WebSocket, game_code: str, player_name: str):
    """WebSocket endpoint for players."""
    await websocket.accept()

    game_code = game_code.upper()
    game = games.get(game_code)
    if not game:
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close(code=4004)
        return

    normalized_name = player_name.strip()
    existing_player = next(
        (p for p in game.players.values() if p.name.casefold() == normalized_name.casefold()),
        None,
    )

    if existing_player:
        player = existing_player
        player.websocket = websocket
        player.connected = True
        player_id = player.id
        rejoined = True
    else:
        if game.phase != GamePhase.LOBBY:
            await websocket.send_json({"type": "error", "message": "Game already started"})
            await websocket.close(code=4003)
            return

        player_id = str(uuid.uuid4())
        player = Player(id=player_id, name=normalized_name or player_name, websocket=websocket)
        game.players[player_id] = player
        rejoined = False

    # Broadcast updated player list
    await broadcast_player_list(game)

    # Send confirmation to player
    await websocket.send_json({
        "type": "joined",
        "player_id": player_id,
        "game_code": game.code,
    })

    await append_event({
        "event": "player_join",
        "game_code": game.code,
        "player_id": player_id,
        "player_name": player.name,
        "rejoin": rejoined,
        "phase": game.phase.value,
    })
    await save_state()

    if game.phase != GamePhase.LOBBY:
        await send_current_state_to_player(websocket, game, player)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "answer":
                if game.phase == GamePhase.QUESTION and player.current_answer is None:
                    answer_index = data.get("answer_index")
                    question = game.current_question()
                    if (
                        question
                        and isinstance(answer_index, int)
                        and 0 <= answer_index < len(question.options)
                    ):
                        answer_ts = time.time()
                        question_start_ts = game.question_start_time
                        player.current_answer = answer_index
                        player.answer_time = (
                            answer_ts - question_start_ts
                            if question_start_ts is not None
                            else None
                        )

                        # Calculate and award score
                        points = 0
                        score_before = player.score
                        if question and player.current_answer == question.correct_index:
                            points = calculate_score(True, player.answer_time or 0.0)
                            player.score += points
                        score_after = player.score

                        if player.answer_time is not None:
                            player.total_answer_time += player.answer_time
                            player.answers_count += 1
                        player.last_answer_time = player.answer_time
                        player.last_answer_index = answer_index
                        player.last_answer_correct = (player.current_answer == question.correct_index) if question else None
                        player.last_answer_ts = answer_ts
                        player.last_answer_question_index = game.current_question_index

                        if question:
                            await append_event({
                                "event": "answer_submitted",
                                "game_code": game.code,
                                "player_id": player.id,
                                "player_name": player.name,
                                "question_index": game.current_question_index,
                                "question_number": game.current_question_index + 1,
                                "question_id": question.id,
                                "question_text": question.text,
                                "options": question.options,
                                "correct_index": question.correct_index,
                                "answer_index": answer_index,
                                "answer_text": question.options[answer_index],
                                "is_correct": player.current_answer == question.correct_index,
                                "answer_time": player.answer_time,
                                "points_awarded": points,
                            })
                            await append_score({
                                "event": "score_awarded",
                                "game_code": game.code,
                                "player_id": player.id,
                                "player_name": player.name,
                                "question_index": game.current_question_index,
                                "question_id": question.id,
                                "answer_index": answer_index,
                                "is_correct": player.current_answer == question.correct_index,
                                "points_awarded": points,
                                "score_before": score_before,
                                "score_after": score_after,
                                "question_start_ts": question_start_ts,
                                "answer_ts": answer_ts,
                                "seconds_to_respond": player.answer_time,
                                "seconds_from_seen": player.answer_time,
                            })
                        await save_state()

                        # Notify quiz master of answer count
                        answered_count = sum(
                            1 for p in game.players.values()
                            if p.current_answer is not None
                        )
                        total_players = len(game.players)
                        players_payload = [p.to_dict() for p in game.players.values()]
                        group_score = sum(p.score for p in game.players.values())
                        await broadcast_to_quiz_master(game, {
                            "type": "answer_received",
                            "answered_count": answered_count,
                            "total_players": total_players,
                            "remaining_count": max(0, total_players - answered_count),
                            "players": players_payload,
                            "group_score": group_score,
                        })
                        await broadcast_to_players(game, {
                            "type": "answer_progress",
                            "answered_count": answered_count,
                            "total_players": total_players,
                            "remaining_count": max(0, total_players - answered_count),
                        })

                        # Confirm to player
                        await websocket.send_json({
                            "type": "answer_confirmed",
                            "answer_index": answer_index,
                        })

    except WebSocketDisconnect:
        if player_id in game.players:
            player = game.players[player_id]
            player.connected = False
            player.websocket = None
            await append_event({
                "event": "player_disconnect",
                "game_code": game.code,
                "player_id": player_id,
                "player_name": player.name,
                "phase": game.phase.value,
            })
            await save_state()
            await broadcast_player_list(game)
