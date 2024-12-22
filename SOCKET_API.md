# Socket.IO Game API Documentation

This document describes the Socket.IO events used for communication between clients and the server in the word guessing game.

## Client → Server Events

### Game Setup
#### `create_game`
- **Description**: Request to create a new game
- **Payload**:
  ```typescript
  {
    playerName: string;  // Name of the host player
  }
  ```

#### `join_game`
- **Description**: Request to join an existing game
- **Payload**:
  ```typescript
  {
    gameCode: string;   // Game code to join
    playerName: string; // Name of the joining player
  }
  ```

#### `start_game`
- **Description**: Host's request to start the game
- **Payload**: Empty object `{}`

### Gameplay
#### `add_word`
- **Description**: Player adds a word to the sentence
- **Payload**:
  ```typescript
  {
    word: string; // The word to add
  }
  ```

#### `make_guess`
- **Description**: Guesser attempts to guess the subject
- **Payload**:
  ```typescript
  {
    guess: string; // The guessed word
  }
  ```

## Server → Client Events

### Connection Status
#### `connect`
- **Description**: Emitted when a client successfully connects to the server
- **Payload**: None

#### `disconnect`
- **Description**: Emitted when a client disconnects from the server
- **Payload**: None

### Game Setup Responses
#### `game_created`
- **Description**: Confirmation that a game was created
- **Broadcast**: No (sent only to creator)
- **Payload**:
  ```typescript
  {
    gameCode: string;    // Unique game code for others to join
    players: {          // List of players in the game
      name: string;     // Player name
      color: string;    // Player's color (hex code)
      isHost: boolean;  // Whether this player is the host
    }[];
  }
  ```

#### `player_joined`
- **Description**: Broadcast when a new player joins the game
- **Broadcast**: Yes (to all players in game)
- **Payload**:
  ```typescript
  {
    gameCode: string;   // Game code
    players: {         // Updated list of all players
      name: string;    // Player name
      color: string;   // Player's color
      isHost: boolean; // Whether this player is the host
    }[];
  }
  ```

#### `player_left`
- **Description**: Broadcast when a player leaves the game
- **Broadcast**: Yes (to all remaining players)
- **Payload**:
  ```typescript
  {
    players: string[]; // Array of remaining player names
  }
  ```

### Game State Updates
#### `game_started`
- **Description**: Broadcast that the game has started
- **Broadcast**: Yes (customized for each player)
- **Payload**:
  ```typescript
  {
    isGuesser: boolean;     // Whether this client is the guesser
    subject: string | null; // The secret word (null for guesser)
    currentTurn: string;    // Name of player whose turn it is
    players: {
      name: string;        // Player name
      color: string;       // Player's color
      isGuesser: boolean; // Whether this player is the guesser
      isHost: boolean;    // Whether this player is the host
    }[];
  }
  ```

#### `sentence_updated`
- **Description**: Broadcast when the sentence changes
- **Broadcast**: Yes (to all players)
- **Payload**:
  ```typescript
  {
    sentence: {          // Array of words in the sentence
      word: string;      // The word
      color: string;     // Color of the player who added it
      player: string;    // Name of the player who added it
    }[];
    currentTurn: string; // Name of player whose turn it is
    subject: string;     // The secret word (null for guesser)
    players: {          // Current player information
      name: string;
      color: string;
      isGuesser: boolean;
      isHost: boolean;
    }[];
  }
  ```

#### `guess_result`
- **Description**: Broadcast when a guess is made
- **Broadcast**: Yes (to all players)
- **Payload**:
  ```typescript
  {
    correct: boolean;  // Whether the guess was correct
    guesser: string;  // Name of the player who made the guess
  }
  ```

#### `game_ended`
- **Description**: Broadcast when the game ends (correct guess)
- **Broadcast**: Yes (to all players)
- **Payload**:
  ```typescript
  {
    winner: string;           // Name of the winning player
    subject: string;         // The secret word
    sentence: string;        // The complete sentence
    scores: {               // Final scores
      [playerName: string]: number;
    };
  }
  ```

### Error Handling
#### `error`
- **Description**: Sent when an error occurs
- **Broadcast**: No (sent only to affected client)
- **Payload**:
  ```typescript
  {
    message: string; // Error message
  }
  ```

## Error Messages
The server may return the following error messages in the `error` event:

### Game Setup Errors
- "You are already in a game"
- "Game not found"
- "Game has already started"
- "Name already taken"
- "Need at least 2 players to start"
- "Only host can start the game"

### Gameplay Errors
- "Game is not in playing state"
- "Not your turn"
- "Invalid word - only letters are allowed"
- "Not a valid English word"
- "You are not the guesser"
  