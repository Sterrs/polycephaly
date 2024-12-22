import socketio
import time
import random
import os
from openai import OpenAI
from concurrent.futures import ProcessPoolExecutor
import sys
import argparse
from typing import Optional
from logging_utils import setup_logger, log_socket_event, log_api_call

# Default model for AI interactions
MODEL = "gpt-4o-mini"

class GameError(Exception):
    """Base class for game-related errors"""
    pass

class AIPlayer:
    def __init__(self, name: str, game_code: str, max_retries: int = 3, retry_delay: float = 2.0):
        self.name = name
        self.game_code = game_code
        self.logger = setup_logger(f'ai_player_{name}', f'ai_player_{name}.log')
        self.logger.info(f"Initializing AI player {name} for game {game_code}")
        
        self.sio = socketio.Client()
        self.is_guesser = False
        self.subject = None
        self.current_sentence = []
        self.my_turn = False
        self.connected = False
        self.in_game = False
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_error = None
        self.game_ended = False
        self.openai_client = OpenAI()  # Make sure OPENAI_API_KEY is set in environment

        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('game_started', self.on_game_started)
        self.sio.on('sentence_updated', self.on_sentence_updated)
        self.sio.on('guess_result', self.on_guess_result)
        self.sio.on('game_ended', self.on_game_ended)
        self.sio.on('error', self.on_error)
        self.sio.on('player_left', self.on_player_left)

    def connect_and_join(self) -> bool:
        """Connect to the server and join the game with retry logic"""
        retries = 0
        while retries < self.max_retries:
            try:
                if not self.connected:
                    self.logger.info("Attempting to connect to server")
                    self.sio.connect('http://localhost:5000')
                    self.connected = True
                
                if not self.in_game:
                    join_data = {
                        'gameCode': self.game_code,
                        'playerName': self.name
                    }
                    log_socket_event(self.logger, "SENDING", "join_game", join_data)
                    self.sio.emit('join_game', join_data)
                return True
            except Exception as e:
                retries += 1
                self.logger.error(f"Connection attempt {retries} failed: {e}")
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"Failed to connect after {self.max_retries} attempts")
                    return False
        return False

    def on_connect(self):
        log_socket_event(self.logger, "RECEIVED", "connect")
        self.logger.info("Connected to server")
        self.connected = True

    def on_disconnect(self):
        log_socket_event(self.logger, "RECEIVED", "disconnect")
        self.logger.info("Disconnected from server")
        self.connected = False
        self.in_game = False
        
        # Try to reconnect if disconnected unexpectedly
        if not self.game_ended:
            self.logger.info("Attempting to reconnect...")
            self.connect_and_join()

    def on_game_started(self, data):
        log_socket_event(self.logger, "RECEIVED", "game_started", data)
        self.is_guesser = data['isGuesser']
        self.subject = data.get('subject')
        self.in_game = True
        self.logger.info(f"Game started. Role: {'Guesser' if self.is_guesser else 'Word Builder'}")
        if not self.is_guesser:
            self.logger.info(f"Subject is: {self.subject}")

    def on_sentence_updated(self, data):
        log_socket_event(self.logger, "RECEIVED", "sentence_updated", data)
        try:
            self.current_sentence = data['sentence']
            current_turn = data['currentTurn']
            self.my_turn = current_turn == self.name
            
            current_text = ' '.join(word_data['word'] for word_data in self.current_sentence)
            self.logger.info(f"Current sentence: {current_text}")
            self.logger.info(f"Current turn: {current_turn} (my turn: {self.my_turn})")

            if self.is_guesser:
                # Calculate probability of guessing based on sentence length
                # Start with 20% chance at 2 words, increasing to 100% at 10 words
                sentence_length = len(self.current_sentence)
                if sentence_length >= 2:
                    base_probability = min(1.0, (sentence_length - 1) * 0.125)  # Reaches 1.0 at 9 words
                    should_guess = random.random() < base_probability
                    
                    if should_guess:
                        self.logger.info(f"Deciding to guess with probability {base_probability:.2f} at {sentence_length} words")
                        self.make_guess()
                    else:
                        self.logger.info(f"Deciding not to guess with probability {base_probability:.2f} at {sentence_length} words")
            elif self.my_turn:
                self.add_word()
        except Exception as e:
            self.logger.error(f"Error handling sentence update: {e}")

    def on_guess_result(self, data):
        log_socket_event(self.logger, "RECEIVED", "guess_result", data)
        if not data['correct'] and self.is_guesser:
            self.logger.info("Incorrect guess, trying again after delay")
            time.sleep(self.retry_delay)
            self.make_guess()

    def on_game_ended(self, data):
        log_socket_event(self.logger, "RECEIVED", "game_ended", data)
        self.logger.info(f"Game ended! Winner: {data['winner']}")
        self.logger.info(f"Final sentence: {data['sentence']}")
        self.logger.info(f"Subject was: {data['subject']}")
        self.game_ended = True
        self.in_game = False
        self.sio.disconnect()

    def on_error(self, data):
        log_socket_event(self.logger, "RECEIVED", "error", data)
        error_msg = data.get('message', 'Unknown error')
        self.logger.error(f"Error: {error_msg}")
        self.last_error = error_msg
        
        # Handle specific error cases
        if "already in a game" in error_msg.lower():
            self.in_game = True
        elif "game not found" in error_msg.lower():
            self.logger.error(f"Invalid game code: {self.game_code}")
            self.sio.disconnect()
        elif "game has already started" in error_msg.lower():
            self.logger.error("Game already in progress")
            self.sio.disconnect()
        elif "name already taken" in error_msg.lower():
            old_name = self.name
            self.name = f"{self.name}_{random.randint(1, 999)}"
            self.logger.info(f"Name {old_name} taken, retrying with {self.name}")
            self.connect_and_join()
        elif "not your turn" in error_msg.lower():
            self.my_turn = False

    def on_player_left(self, data):
        log_socket_event(self.logger, "RECEIVED", "player_left", data)
        self.logger.info(f"Player left. Remaining players: {', '.join(data['players'])}")

    def add_word(self):
        """Add a word to the sentence with retry logic for invalid words"""
        retries = 0
        while retries < self.max_retries and self.my_turn:
            try:
                current_text = ' '.join(word_data['word'] for word_data in self.current_sentence)
                
                # Include any previous error in the prompt
                error_context = ""
                if self.last_error:
                    error_context = f"\nPrevious attempt failed: {self.last_error}"
                
                prompt = f"""You are playing a word game. The secret subject is "{self.subject}".
Current sentence: "{current_text}"
Generate a single word that would help describe the subject without making it too obvious.
The word should be a valid English word and contain only letters. Respond with just the word, nothing else.
Make sure the word is common and simple.{error_context}"""

                self.logger.info("Requesting word from OpenAI API")
                params = {
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.7
                }
                log_api_call(self.logger, "POST", "/chat/completions", params)
                response = self.openai_client.chat.completions.create(**params)
                word = response.choices[0].message.content.strip().lower()
                self.logger.info(f"Generated word: {word}")
                
                self.last_error = None  # Clear any previous error
                emit_data = {'word': word}
                log_socket_event(self.logger, "SENDING", "add_word", emit_data)
                self.sio.emit('add_word', emit_data)
                break
            except Exception as e:
                retries += 1
                self.logger.error(f"Error generating word (attempt {retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    # Fallback to a simple word if all retries fail
                    fallback_words = ['the', 'is', 'a', 'an', 'it']
                    fallback_word = random.choice(fallback_words)
                    self.logger.info(f"Using fallback word: {fallback_word}")
                    emit_data = {'word': fallback_word}
                    log_socket_event(self.logger, "SENDING", "add_word", emit_data)
                    self.sio.emit('add_word', emit_data)

    def make_guess(self):
        """Make a guess with retry logic"""
        retries = 0
        while retries < self.max_retries and self.my_turn:
            try:
                current_text = ' '.join(word_data['word'] for word_data in self.current_sentence)
                
                # Include any previous error in the prompt
                error_context = ""
                if self.last_error:
                    error_context = f"\nPrevious attempt failed: {self.last_error}"
                
                prompt = f"""You are playing a word guessing game. Players are building a sentence to describe a secret subject.
Current sentence: "{current_text}"
Based on this sentence, what do you think is the secret subject?
Your guess can be a single word or multiple words. Respond with just your guess, nothing else.
The subject could be anything - a common word, a phrase, a name, etc.{error_context}"""

                self.logger.info("Requesting guess from OpenAI API")
                params = {
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 20,
                    "temperature": 0.3
                }
                log_api_call(self.logger, "POST", "/chat/completions", params)
                response = self.openai_client.chat.completions.create(**params)
                guess = response.choices[0].message.content.strip().lower()
                self.logger.info(f"Generated guess: {guess}")
                
                self.last_error = None  # Clear any previous error
                emit_data = {'guess': guess}
                log_socket_event(self.logger, "SENDING", "make_guess", emit_data)
                self.sio.emit('make_guess', emit_data)
                break
            except Exception as e:
                retries += 1
                self.logger.error(f"Error generating guess (attempt {retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)

def run_ai_player(name: str, game_code: str):
    player = AIPlayer(name, game_code)
    if player.connect_and_join():
        try:
            # Keep the process running until the game ends
            while not getattr(player, 'game_ended', False):
                time.sleep(1)
        except KeyboardInterrupt:
            player.logger.info("Received interrupt, disconnecting")
            player.sio.disconnect()
        player.logger.info("AI player process ending")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run AI players for the word guessing game')
    parser.add_argument('-n', '--num_players', type=int, default=4,
                       help='Number of AI players to create (default: 4)')
    args = parser.parse_args()

    game_code = input("Enter game code: ")
    ai_names = [f"AI_Player_{i+1}" for i in range(args.num_players)]
    
    # Start AI players in separate processes
    with ProcessPoolExecutor(max_workers=args.num_players) as executor:
        futures = [
            executor.submit(run_ai_player, name, game_code)
            for name in ai_names
        ]
        
        try:
            # Wait for all processes to complete
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            print("Shutting down AI players...")
            executor.shutdown(wait=False)
