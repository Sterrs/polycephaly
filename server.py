from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
from datetime import datetime
import random
from typing import Dict, List, Set
import re
from logging_utils import setup_logger, log_socket_event

# Set up logger
logger = setup_logger('server', 'server.log')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state
games: Dict[str, dict] = {}  # Store game states
players: Dict[str, str] = {}  # Map player SIDs to game codes
connected_users: Set[str] = set()  # Track connected user session IDs

# Load targets from file
with open('data/targets.txt', 'r') as f:
    TARGETS = [line.strip() for line in f if line.strip()]
    logger.info(f"Loaded {len(TARGETS)} targets")

# Load wordlist from file
with open('data/words_alpha.txt', 'r') as f:
    VALID_WORDS = {line.strip().lower() for line in f if line.strip()}
    logger.info(f"Loaded {len(VALID_WORDS)} valid words")

# Regex pattern for word validation - only letters allowed
WORD_PATTERN = re.compile(r'^[a-zA-Z]+$')

# Pastel colors for players
PLAYER_COLORS = [
    '#FFB3BA',  # pastel pink
    '#BAFFC9',  # pastel green
    '#BAE1FF',  # pastel blue
    '#FFFFBA',  # pastel yellow
    '#FFB3FF',  # pastel purple
    '#FFD9BA',  # pastel orange
]

@app.route('/')
def index():
    logger.info(f"Index page requested from {request.remote_addr}")
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    session['connected'] = True

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    logger.info(f"Client disconnecting: {sid}")
    if sid in players:
        game_code = players[sid]
        if game_code in games:
            game = games[game_code]
            # Remove player from game
            game['players'] = [p for p in game['players'] if p['sid'] != sid]
            # If no players left, remove the game
            if not game['players']:
                logger.info(f"Game {game_code} ended - no players remaining")
                del games[game_code]
            else:
                # Notify remaining players
                remaining_players = [p['name'] for p in game['players']]
                logger.info(f"Player left game {game_code}. Remaining: {remaining_players}")
                emit('player_left', {
                    'players': remaining_players
                }, room=game_code)
        del players[sid]
    connected_users.discard(sid)

@socketio.on('create_game')
def on_create_game(data):
    sid = request.sid
    log_socket_event(logger, "RECEIVED", "create_game", data)
    
    if sid in players:
        error_msg = {'message': 'You are already in a game'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return

    game_code = generate_game_code()
    host_name = data.get('playerName')
    
    games[game_code] = {
        'players': [{
            'name': host_name,
            'sid': sid,
            'score': 0,
            'is_host': True,
            'color': PLAYER_COLORS[0]
        }],
        'current_sentence': [],
        'current_turn_index': 0,
        'guesser_index': None,
        'subject': None,
        'state': 'waiting'
    }
    
    players[sid] = game_code
    connected_users.add(sid)
    join_room(game_code)
    
    response_data = {
        'gameCode': game_code,
        'players': [{
            'name': host_name,
            'color': PLAYER_COLORS[0],
            'isHost': True
        }]
    }
    log_socket_event(logger, "SENT", "game_created", response_data)
    emit('game_created', response_data)

@socketio.on('join_game')
def on_join_game(data):
    sid = request.sid
    log_socket_event(logger, "RECEIVED", "join_game", data)
    
    if sid in players:
        error_msg = {'message': 'You are already in a game'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return

    game_code = data.get('gameCode')
    player_name = data.get('playerName')
    
    if game_code not in games:
        error_msg = {'message': 'Game not found'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    game = games[game_code]
    if game['state'] != 'waiting':
        error_msg = {'message': 'Game has already started'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return

    if any(p['name'] == player_name for p in game['players']):
        error_msg = {'message': 'Name already taken'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    # Assign next available color
    player_color = PLAYER_COLORS[len(game['players']) % len(PLAYER_COLORS)]
    
    game['players'].append({
        'name': player_name,
        'sid': sid,
        'score': 0,
        'is_host': False,
        'color': player_color
    })
    
    players[sid] = game_code
    connected_users.add(sid)
    join_room(game_code)
    
    # Send updated player list with colors
    player_info = [{
        'name': p['name'],
        'color': p['color'],
        'isHost': p['is_host']
    } for p in game['players']]
    
    response_data = {
        'players': player_info,
        'gameCode': game_code
    }
    log_socket_event(logger, "SENT", "player_joined", response_data)
    emit('player_joined', response_data, room=game_code)

@socketio.on('start_game')
def on_start_game(data):
    sid = request.sid
    log_socket_event(logger, "RECEIVED", "start_game", data)
    
    game_code = players.get(sid)
    if not game_code or game_code not in games:
        error_msg = {'message': 'Game not found'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    game = games[game_code]
    if not any(p['sid'] == sid and p['is_host'] for p in game['players']):
        error_msg = {'message': 'Only host can start the game'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
    
    if len(game['players']) < 2:
        error_msg = {'message': 'Need at least 2 players to start'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    game['state'] = 'playing'
    game['subject'] = random.choice(TARGETS)
    logger.info(f"Game {game_code} started with subject: {game['subject']}")
    
    # Randomly select guesser
    game['guesser_index'] = random.randint(0, len(game['players']) - 1)
    guesser_name = game['players'][game['guesser_index']]['name']
    logger.info(f"Selected guesser: {guesser_name}")
    
    # Set first turn to the player after the guesser
    game['current_turn_index'] = (game['guesser_index'] + 1) % len(game['players'])
    first_turn_player = game['players'][game['current_turn_index']]['name']
    
    # Prepare player info for all players
    player_info = [{
        'name': p['name'],
        'color': p['color'],
        'isGuesser': game['players'].index(p) == game['guesser_index'],
        'isHost': p['is_host']
    } for p in game['players']]
    
    # Send different information to guesser and other players
    for player in game['players']:
        if game['players'].index(player) == game['guesser_index']:
            response_data = {
                'isGuesser': True,
                'subject': None,
                'currentTurn': first_turn_player,
                'players': player_info
            }
        else:
            response_data = {
                'isGuesser': False,
                'subject': game['subject'],
                'currentTurn': first_turn_player,
                'players': player_info
            }
        log_socket_event(logger, "SENT", "game_started", response_data)
        emit('game_started', response_data, room=player['sid'])
    
    # Send initial sentence state to all players
    sentence_data = {
        'sentence': game['current_sentence'],
        'currentTurn': first_turn_player,
        'subject': game['subject'],
        'players': player_info
    }
    log_socket_event(logger, "SENT", "sentence_updated", sentence_data)
    emit('sentence_updated', sentence_data, room=game_code)

@socketio.on('add_word')
def on_add_word(data):
    sid = request.sid
    log_socket_event(logger, "RECEIVED", "add_word", data)
    
    game_code = players.get(sid)
    if not game_code or game_code not in games:
        error_msg = {'message': 'Game not found'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    game = games[game_code]
    if game['state'] != 'playing':
        error_msg = {'message': 'Game is not in playing state'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    player_index = next((i for i, p in enumerate(game['players']) if p['sid'] == sid), None)
    if player_index != game['current_turn_index']:
        error_msg = {'message': 'Not your turn'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    word = data.get('word', '').strip()
    if not word or not WORD_PATTERN.match(word):
        error_msg = {'message': f'Invalid word "{word}" - only letters are allowed'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return

    # Verify the word is in our wordlist
    if word.lower() not in VALID_WORDS:
        error_msg = {'message': f'"{word}" is not a valid English word'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    # Store word with player's color
    player_color = game['players'][player_index]['color']
    game['current_sentence'].append({
        'word': word,
        'color': player_color,
        'player': game['players'][player_index]['name']
    })
    logger.info(f"Word added to game {game_code}: {word}")
    
    game['current_turn_index'] = (game['current_turn_index'] + 1) % len(game['players'])
    if game['current_turn_index'] == game['guesser_index']:
        game['current_turn_index'] = (game['current_turn_index'] + 1) % len(game['players'])
        
    # Prepare player info
    player_info = [{
        'name': p['name'],
        'color': p['color'],
        'isGuesser': game['players'].index(p) == game['guesser_index'],
        'isHost': p['is_host']
    } for p in game['players']]
    
    response_data = {
        'sentence': game['current_sentence'],
        'currentTurn': game['players'][game['current_turn_index']]['name'],
        'subject': game['subject'],
        'players': player_info
    }
    log_socket_event(logger, "SENT", "sentence_updated", response_data)
    emit('sentence_updated', response_data, room=game_code)

@socketio.on('make_guess')
def on_make_guess(data):
    sid = request.sid
    log_socket_event(logger, "RECEIVED", "make_guess", data)
    
    game_code = players.get(sid)
    if not game_code or game_code not in games:
        error_msg = {'message': 'Game not found'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    game = games[game_code]
    if game['state'] != 'playing':
        error_msg = {'message': 'Game is not in playing state'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    player_index = next((i for i, p in enumerate(game['players']) if p['sid'] == sid), None)
    if player_index != game['guesser_index']:
        error_msg = {'message': 'You are not the guesser'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return
        
    guess = data.get('guess', '').strip().lower()
    if not guess:
        error_msg = {'message': 'Guess cannot be empty'}
        log_socket_event(logger, "SENT", "error", error_msg)
        emit('error', error_msg)
        return

    # Only check if the guess matches the subject
    correct = guess == game['subject'].lower()
    logger.info(f"Guess in game {game_code}: {guess} (correct: {correct})")
    
    if correct:
        game['players'][player_index]['score'] += 10
        game['state'] = 'finished'
        
        # Create final sentence with words only
        final_sentence = ' '.join(word_data['word'] for word_data in game['current_sentence'])
        
        # Send game ended event
        response_data = {
            'winner': game['players'][player_index]['name'],
            'subject': game['subject'],
            'sentence': final_sentence,
            'scores': {p['name']: p['score'] for p in game['players']}
        }
        log_socket_event(logger, "SENT", "game_ended", response_data)
        emit('game_ended', response_data, room=game_code)
        
        logger.info(f"Game {game_code} ended. Winner: {game['players'][player_index]['name']}")
        
        # Clean up the game
        for player in game['players']:
            leave_room(game_code, player['sid'])
            if player['sid'] in players:
                del players[player['sid']]
            if player['sid'] in connected_users:
                connected_users.discard(player['sid'])
        
        # Remove the game
        if game_code in games:
            del games[game_code]
    else:
        response_data = {
            'correct': False,
            'guesser': game['players'][player_index]['name']
        }
        log_socket_event(logger, "SENT", "guess_result", response_data)
        emit('guess_result', response_data, room=game_code)

def generate_game_code() -> str:
    """Generate a unique 4-digit game code."""
    timestamp = datetime.now().strftime('%f')  # microseconds
    return f"{int(timestamp) % 10000:04d}"  # Take last 4 digits and pad with zeros

if __name__ == '__main__':
    logger.info("Starting server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 