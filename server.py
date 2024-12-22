from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
from datetime import datetime
import random
from typing import Dict, List, Set
import re

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

# Load wordlist from file
with open('data/wordlist.txt', 'r') as f:
    VALID_WORDS = {line.strip().lower() for line in f if line.strip()}

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
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    session['connected'] = True

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in players:
        game_code = players[sid]
        if game_code in games:
            game = games[game_code]
            # Remove player from game
            game['players'] = [p for p in game['players'] if p['sid'] != sid]
            # If no players left, remove the game
            if not game['players']:
                del games[game_code]
            else:
                # Notify remaining players
                emit('player_left', {
                    'players': [p['name'] for p in game['players']]
                }, room=game_code)
        del players[sid]
    connected_users.discard(sid)

@socketio.on('create_game')
def on_create_game(data):
    sid = request.sid
    if sid in players:
        emit('error', {'message': 'You are already in a game'})
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
        'current_sentence': [],  # Will store tuples of (word, player_color)
        'current_turn_index': 0,
        'guesser_index': None,
        'subject': None,
        'state': 'waiting'
    }
    
    players[sid] = game_code
    connected_users.add(sid)
    join_room(game_code)
    emit('game_created', {
        'gameCode': game_code,
        'players': [{
            'name': host_name,
            'color': PLAYER_COLORS[0],
            'isHost': True
        }]
    })

@socketio.on('join_game')
def on_join_game(data):
    sid = request.sid
    if sid in players:
        emit('error', {'message': 'You are already in a game'})
        return

    game_code = data.get('gameCode')
    player_name = data.get('playerName')
    
    if game_code not in games:
        emit('error', {'message': 'Game not found'})
        return
        
    game = games[game_code]
    if game['state'] != 'waiting':
        emit('error', {'message': 'Game has already started'})
        return

    if any(p['name'] == player_name for p in game['players']):
        emit('error', {'message': 'Name already taken'})
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
    
    emit('player_joined', {
        'players': player_info,
        'gameCode': game_code
    }, room=game_code)

@socketio.on('start_game')
def on_start_game(data):
    sid = request.sid
    game_code = players.get(sid)
    
    if not game_code or game_code not in games:
        emit('error', {'message': 'Game not found'})
        return
        
    game = games[game_code]
    if not any(p['sid'] == sid and p['is_host'] for p in game['players']):
        emit('error', {'message': 'Only host can start the game'})
        return
    
    if len(game['players']) < 2:
        emit('error', {'message': 'Need at least 2 players to start'})
        return
        
    game['state'] = 'playing'
    game['subject'] = random.choice(TARGETS)  # Randomly select a target
    
    # Randomly select guesser
    game['guesser_index'] = random.randint(0, len(game['players']) - 1)
    
    # Set first turn to the player after the guesser
    game['current_turn_index'] = (game['guesser_index'] + 1) % len(game['players'])
    
    # Send different information to guesser and other players
    first_turn_player = game['players'][game['current_turn_index']]['name']
    
    # Prepare player info for all players
    player_info = [{
        'name': p['name'],
        'color': p['color'],
        'isGuesser': game['players'].index(p) == game['guesser_index'],
        'isHost': p['is_host']
    } for p in game['players']]
    
    for player in game['players']:
        if game['players'].index(player) == game['guesser_index']:
            emit('game_started', {
                'isGuesser': True,
                'subject': None,
                'currentTurn': first_turn_player,
                'players': player_info
            }, room=player['sid'])
        else:
            emit('game_started', {
                'isGuesser': False,
                'subject': game['subject'],
                'currentTurn': first_turn_player,
                'players': player_info
            }, room=player['sid'])
    
    # Send initial sentence state to all players
    emit('sentence_updated', {
        'sentence': game['current_sentence'],
        'currentTurn': first_turn_player,
        'subject': game['subject'],
        'players': player_info
    }, room=game_code)

@socketio.on('add_word')
def on_add_word(data):
    sid = request.sid
    game_code = players.get(sid)
    
    if not game_code or game_code not in games:
        emit('error', {'message': 'Game not found'})
        return
        
    game = games[game_code]
    if game['state'] != 'playing':
        emit('error', {'message': 'Game is not in playing state'})
        return
        
    player_index = next((i for i, p in enumerate(game['players']) if p['sid'] == sid), None)
    if player_index != game['current_turn_index']:
        emit('error', {'message': 'Not your turn'})
        return
        
    word = data.get('word', '').strip()
    if not word or not WORD_PATTERN.match(word):
        emit('error', {'message': 'Invalid word - only letters are allowed'})
        return

    # Verify the word is in our wordlist
    if word.lower() not in VALID_WORDS:
        emit('error', {'message': 'Not a valid English word'})
        return
        
    # Store word with player's color
    player_color = game['players'][player_index]['color']
    game['current_sentence'].append({
        'word': word,
        'color': player_color,
        'player': game['players'][player_index]['name']
    })
    
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
    
    emit('sentence_updated', {
        'sentence': game['current_sentence'],
        'currentTurn': game['players'][game['current_turn_index']]['name'],
        'subject': game['subject'],
        'players': player_info
    }, room=game_code)

@socketio.on('make_guess')
def on_make_guess(data):
    sid = request.sid
    game_code = players.get(sid)
    
    if not game_code or game_code not in games:
        emit('error', {'message': 'Game not found'})
        return
        
    game = games[game_code]
    if game['state'] != 'playing':
        emit('error', {'message': 'Game is not in playing state'})
        return
        
    player_index = next((i for i, p in enumerate(game['players']) if p['sid'] == sid), None)
    if player_index != game['guesser_index']:
        emit('error', {'message': 'You are not the guesser'})
        return
        
    guess = data.get('guess', '').strip().lower()
    correct = guess == game['subject'].lower()
    
    if correct:
        game['players'][player_index]['score'] += 10
        game['state'] = 'finished'
        
        # Create final sentence with words only
        final_sentence = ' '.join(word_data['word'] for word_data in game['current_sentence'])
        
        # Send game ended event
        emit('game_ended', {
            'winner': game['players'][player_index]['name'],
            'subject': game['subject'],
            'sentence': final_sentence,
            'scores': {p['name']: p['score'] for p in game['players']}
        }, room=game_code)
        
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
        emit('guess_result', {
            'correct': False,
            'guesser': game['players'][player_index]['name']
        }, room=game_code)

def generate_game_code() -> str:
    """Generate a unique 4-digit game code."""
    timestamp = datetime.now().strftime('%f')  # microseconds
    return f"{int(timestamp) % 10000:04d}"  # Take last 4 digits and pad with zeros

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 