# Polycephaly - Game Overview

## Game Concept

Polycephaly is a collaborative word game that combines elements of word association, creative storytelling, and deduction. The name "Polycephaly" refers to having multiple heads, reflecting the game's collaborative nature where multiple players work together (and sometimes against each other) to create meaningful sentences.

### Core Gameplay

1. **Players and Roles**
   - Multiple players can join a game using a unique game code
   - One player is randomly selected as the "Guesser"
   - All other players are "Word Builders"
   - The host (game creator) initiates the game

2. **Game Flow**
   - At the start of each game, a subject is chosen (e.g., "James Bond")
   - The subject is revealed to all Word Builders but hidden from the Guesser
   - Players take turns adding one word at a time to construct a sentence
   - The sentence should describe or relate to the hidden subject
   - The Guesser can attempt to guess the subject at any time
   - The game continues until the Guesser correctly identifies the subject

3. **Turn Structure**
   - Word Builders take turns in sequence
   - Each turn, a player can add exactly one word to the sentence
   - The Guesser is skipped in the turn rotation
   - Players must wait for their turn to add a word

4. **Scoring System**
   - The Guesser earns 10 points for correctly guessing the subject
   - The game tracks scores for all players
   - Final scores are displayed when the game ends

## Technical Implementation

### Architecture

1. **Backend (Python/Flask)**
   - Flask server handles HTTP requests and WebSocket connections
   - Flask-SocketIO manages real-time communication
   - Game state management using in-memory dictionaries
   - Type hints and data structures for game state

2. **Frontend (Vanilla JavaScript)**
   - Pure JavaScript without frameworks
   - Socket.IO client for real-time updates
   - Responsive design with CSS
   - Mobile-friendly interface

3. **Real-time Communication**
   - WebSocket events for game actions
   - Room-based broadcasting for multi-game support
   - Automatic disconnection handling
   - Error handling and validation

4. **Game State Management**
   - Server-side tracking of game sessions
   - Turn rotation and role management
   - Score tracking and validation
   - Input sanitization and error handling

### User Experience

1. **Game Setup**
   - Host creates a game and receives a unique 4-digit game code
   - Players join using the game code and choose their names
   - Host sees a lobby with connected players and start game option
   - Players wait in a lobby until host starts the game

2. **Gameplay Flow**
   - One player is randomly assigned as the Guesser
   - Word Builders see the subject, Guesser does not
   - Players take turns adding one word to build a sentence
   - Real-time updates show current sentence and turn status
   - Guesser can attempt to identify the subject at any time

3. **Game Conclusion**
   - Game ends when Guesser correctly identifies the subject
   - Final scores are displayed for all players
   - Players can choose to start a new game
