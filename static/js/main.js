// Initialize Socket.IO connection
const socket = io();

// Game state
let isHost = false;
let isGuesser = false;
let currentGameCode = null;
let isInGame = false;  // Track if user is in a game
let playerName = '';   // Store the player's name
let currentTurnName = ''; // Store whose turn it is

// DOM Elements
const pages = {
    landing: document.getElementById('landing-page'),
    createGame: document.getElementById('create-game-form'),
    joinGame: document.getElementById('join-game-form'),
    waitingRoom: document.getElementById('waiting-room'),
    gameRoom: document.getElementById('game-room'),
    gameOver: document.getElementById('game-over')
};

// Navigation functions
function showPage(pageId) {
    // If user is in game, only allow game-related pages
    if (isInGame && pageId === 'landing') {
        return;
    }
    Object.values(pages).forEach(page => page.classList.remove('active'));
    pages[pageId].classList.add('active');
}

// Event Listeners
document.getElementById('create-game-btn').addEventListener('click', () => {
    if (!isInGame) {
        showPage('createGame');
    }
});

document.getElementById('join-game-btn').addEventListener('click', () => {
    if (!isInGame) {
        showPage('joinGame');
    }
});

document.querySelectorAll('.back-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        if (!isInGame) {
            showPage('landing');
        }
    });
});

// Form Submissions
document.getElementById('host-form').addEventListener('submit', (e) => {
    e.preventDefault();
    if (!isInGame) {
        playerName = document.getElementById('host-name').value;
        socket.emit('create_game', { playerName });
        isHost = true;
        
        // Disable form
        document.getElementById('host-name').disabled = true;
        document.getElementById('create-submit-btn').disabled = true;
        
        // Show status
        const statusDiv = document.getElementById('host-status');
        statusDiv.textContent = `Creating game as ${playerName}...`;
        statusDiv.style.display = 'block';
    }
});

document.getElementById('join-form').addEventListener('submit', (e) => {
    e.preventDefault();
    if (!isInGame) {
        const gameCode = document.getElementById('game-code').value;
        playerName = document.getElementById('player-name').value;
        socket.emit('join_game', { gameCode, playerName });
        
        // Disable form
        document.getElementById('game-code').disabled = true;
        document.getElementById('player-name').disabled = true;
        document.getElementById('join-submit-btn').disabled = true;
        
        // Show status
        const statusDiv = document.getElementById('join-status');
        statusDiv.textContent = `Joining game as ${playerName}...`;
        statusDiv.style.display = 'block';
    }
});

// Game Controls
document.getElementById('start-game-btn').addEventListener('click', () => {
    if (isHost) {
        socket.emit('start_game', {});
    }
});

function submitWord() {
    const wordInput = document.getElementById('word-input');
    const word = wordInput.value.trim();
    if (word && !isGuesser) {
        // Validate word contains only letters
        if (!/^[a-zA-Z]+$/.test(word)) {
            alert('Words can only contain letters');
            return;
        }
        socket.emit('add_word', { word });
        wordInput.value = '';
    }
}

function submitGuess() {
    const guessInput = document.getElementById('guess-input');
    const guess = guessInput.value.trim();
    if (guess && isGuesser) {
        socket.emit('make_guess', { guess });
        guessInput.value = '';
    }
}

// Add word button click
document.getElementById('add-word-btn').addEventListener('click', submitWord);

// Add word input enter key
document.getElementById('word-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        submitWord();
    }
});

// Prevent non-letter input in word input
document.getElementById('word-input').addEventListener('keydown', (e) => {
    // Allow special keys like backspace, delete, arrows
    if (e.key.length > 1) return;
    
    // Block any character that isn't a letter
    if (!/^[a-zA-Z]$/.test(e.key)) {
        e.preventDefault();
    }
});

// Submit guess button click
document.getElementById('submit-guess-btn').addEventListener('click', submitGuess);

// Submit guess input enter key
document.getElementById('guess-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        submitGuess();
    }
});

document.getElementById('new-game-btn').addEventListener('click', () => {
    if (confirm('Are you sure you want to leave the current game?')) {
        showPage('landing');
        resetGameState();
    }
});

// Socket Event Handlers
socket.on('game_created', (data) => {
    currentGameCode = data.gameCode;
    document.getElementById('displayed-game-code').textContent = data.gameCode;
    isInGame = true;
    
    // Show host controls only for the host
    const hostControls = document.getElementById('host-controls');
    hostControls.style.display = isHost ? 'block' : 'none';
    
    // Update status message
    const statusDiv = document.getElementById('host-status');
    statusDiv.textContent = `Game created! You've joined as ${playerName} (Host)`;
    
    // Update player list with colors
    updatePlayerList(data.players);
    
    showPage('waitingRoom');
});

socket.on('player_joined', (data) => {
    // Update player list with colors
    updatePlayerList(data.players);
    isInGame = true;
    
    // Set the game code for all players
    currentGameCode = data.gameCode;
    document.getElementById('displayed-game-code').textContent = data.gameCode;
    
    // Update status message if we're the one who just joined
    if (document.getElementById('join-status').style.display === 'block') {
        const statusDiv = document.getElementById('join-status');
        statusDiv.textContent = `Successfully joined as ${playerName}!`;
    }
    
    // Show host controls only for the host
    const hostControls = document.getElementById('host-controls');
    hostControls.style.display = isHost ? 'block' : 'none';
    
    showPage('waitingRoom');
});

socket.on('player_left', (data) => {
    const playersList = document.getElementById('players-list');
    playersList.innerHTML = '';
    data.players.forEach(player => {
        const li = document.createElement('li');
        li.textContent = player;
        playersList.appendChild(li);
    });
});

function updateGamePlayersList(players, currentTurn, score) {
    const playersList = document.getElementById('game-players-list');
    playersList.innerHTML = '';
    
    players.forEach(player => {
        const li = document.createElement('li');
        if (player.name === currentTurn) {
            li.classList.add('current-turn');
        }
        
        const playerBubble = document.createElement('span');
        playerBubble.className = 'player-bubble';
        playerBubble.style.backgroundColor = player.color;
        playerBubble.textContent = player.name;
        
        const roleSpan = document.createElement('span');
        roleSpan.className = 'player-role';
        roleSpan.textContent = player.isGuesser ? 'Guesser' : 'Word Builder';
        
        li.appendChild(playerBubble);
        li.appendChild(roleSpan);
        
        // Add "You" indicator if this is the current player
        if (player.name === playerName) {
            const youSpan = document.createElement('span');
            youSpan.className = 'player-indicator';
            youSpan.textContent = '(You)';
            li.appendChild(youSpan);
        }
        
        // Add host indicator
        if (player.isHost) {
            const hostSpan = document.createElement('span');
            hostSpan.className = 'host-indicator';
            hostSpan.textContent = '(Host)';
            li.appendChild(hostSpan);
        }
        
        playersList.appendChild(li);
    });

    // Update score display
    const scoreValue = document.querySelector('#score-display .score-value');
    scoreValue.textContent = score || 0;
}

socket.on('game_started', (data) => {
    isGuesser = data.isGuesser;
    showPage('gameRoom');
    
    // Update player role display
    const roleText = isGuesser ? 'Guesser' : 'Word Builder';
    document.getElementById('player-role').textContent = roleText;
    
    // Set initial turn
    currentTurnName = data.currentTurn;
    
    const wordInputSection = document.getElementById('word-input-section');
    const guessSection = document.getElementById('guess-section');
    
    if (isGuesser) {
        wordInputSection.style.display = 'none';
        guessSection.style.display = 'flex';
        document.getElementById('turn-status').textContent = 'Wait for others to build the sentence';
    } else {
        wordInputSection.style.display = 'flex';
        guessSection.style.display = 'none';
        
        let statusMessage = '';
        if (data.subject) {
            statusMessage = `The subject is: "${data.subject}"`;
        }
        
        // Add turn information to the status message
        if (currentTurnName === playerName) {
            statusMessage += statusMessage ? '\n' : '';
            statusMessage += 'It\'s your turn to add a word!';
        } else {
            statusMessage += statusMessage ? '\n' : '';
            statusMessage += `Waiting for ${currentTurnName} to add a word...`;
        }
        
        const turnStatus = document.getElementById('turn-status');
        turnStatus.style.whiteSpace = 'pre-line';  // Preserve newlines
        turnStatus.textContent = statusMessage;
    }
    
    // Update players list with roles
    updateGamePlayersList(data.players, currentTurnName, data.score);
});

socket.on('sentence_updated', (data) => {
    // Update sentence with colored word bubbles
    const sentenceContainer = document.getElementById('current-sentence');
    sentenceContainer.innerHTML = '';
    
    data.sentence.forEach((wordData, index) => {
        const wordSpan = document.createElement('span');
        wordSpan.textContent = wordData.word;
        wordSpan.className = 'word-bubble';
        wordSpan.style.backgroundColor = wordData.color;
        wordSpan.title = `Added by ${wordData.player}`;
        
        // Add space between words
        if (index > 0) {
            sentenceContainer.appendChild(document.createTextNode(' '));
        }
        
        sentenceContainer.appendChild(wordSpan);
    });
    
    currentTurnName = data.currentTurn;
    
    // Update turn status while preserving subject
    const turnStatus = document.getElementById('turn-status');
    turnStatus.style.whiteSpace = 'pre-line';  // Ensure newlines are preserved
    
    let statusMessage = '';
    if (data.subject) {
        statusMessage = `The subject is: "${data.subject}"`;
    }
    
    // Add turn information
    if (currentTurnName === playerName) {
        if (isGuesser) {
            statusMessage = 'It\'s your turn to guess!';
        } else {
            statusMessage += statusMessage ? '\n' : '';
            statusMessage += 'It\'s your turn to add a word!';
        }
    } else {
        if (isGuesser) {
            statusMessage = 'Wait for others to build the sentence';
        } else {
            statusMessage += statusMessage ? '\n' : '';
            statusMessage += `Waiting for ${currentTurnName} to add a word...`;
        }
    }
    
    turnStatus.textContent = statusMessage;
    
    // Update players list and score
    updateGamePlayersList(data.players, currentTurnName, data.score);
});

socket.on('guess_result', (data) => {
    // Update guess history
    const guessList = document.getElementById('guess-list');
    guessList.innerHTML = ''; // Clear existing guesses
    
    data.guesses.forEach(guessData => {
        const guessDiv = document.createElement('div');
        guessDiv.className = 'guess-entry';
        
        const guessBubble = document.createElement('span');
        guessBubble.className = 'guess-bubble';
        guessBubble.style.backgroundColor = guessData.color;
        guessBubble.textContent = guessData.guess;
        
        const guessTime = document.createElement('span');
        guessTime.className = 'guess-time';
        const timestamp = new Date(guessData.timestamp);
        guessTime.textContent = timestamp.toLocaleTimeString();
        
        guessDiv.appendChild(guessBubble);
        guessDiv.appendChild(guessTime);
        guessList.appendChild(guessDiv);
    });

    // Update player list and score
    if (data.players) {
        updateGamePlayersList(data.players, currentTurnName, data.score);
    }
});

socket.on('game_ended', (data) => {
    showPage('gameOver');
    
    // Update game over information
    document.getElementById('winner-name').textContent = data.winner;
    document.getElementById('final-subject').textContent = data.subject;
    document.getElementById('final-sentence').textContent = data.sentence;
    
    // Update final score
    document.querySelector('#final-score .score-value').textContent = data.score;
    
    // Update final guess history
    const finalGuessList = document.getElementById('final-guess-list');
    finalGuessList.innerHTML = '';
    data.guesses.forEach(guessData => {
        const guessDiv = document.createElement('div');
        guessDiv.className = 'guess-entry';
        
        const guessBubble = document.createElement('span');
        guessBubble.className = 'guess-bubble';
        guessBubble.style.backgroundColor = guessData.color;
        guessBubble.textContent = guessData.guess;
        
        const guessTime = document.createElement('span');
        guessTime.className = 'guess-time';
        const timestamp = new Date(guessData.timestamp);
        guessTime.textContent = timestamp.toLocaleTimeString();
        
        guessDiv.appendChild(guessBubble);
        guessDiv.appendChild(guessTime);
        finalGuessList.appendChild(guessDiv);
    });
    
    // Reset game state
    isInGame = false;
    isHost = false;
    isGuesser = false;
    currentGameCode = null;
    playerName = '';
    currentTurnName = '';
});

socket.on('error', (data) => {
    alert(data.message);
    
    // Re-enable forms if there was an error
    if (document.getElementById('host-status').style.display === 'block') {
        document.getElementById('host-name').disabled = false;
        document.getElementById('create-submit-btn').disabled = false;
        document.getElementById('host-status').style.display = 'none';
    }
    
    if (document.getElementById('join-status').style.display === 'block') {
        document.getElementById('game-code').disabled = false;
        document.getElementById('player-name').disabled = false;
        document.getElementById('join-submit-btn').disabled = false;
        document.getElementById('join-status').style.display = 'none';
    }
});

// Handle disconnection
socket.on('disconnect', () => {
    if (isInGame) {
        alert('You have been disconnected from the game.');
        resetGameState();
        showPage('landing');
    }
});

// Utility Functions
function resetGameState() {
    isHost = false;
    isGuesser = false;
    isInGame = false;
    currentGameCode = null;
    playerName = '';
    currentTurnName = '';
    
    // Reset and enable all form inputs
    const inputs = ['host-name', 'game-code', 'player-name', 'subject-input', 'word-input', 'guess-input'];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.value = '';
            input.disabled = false;
        }
    });
    
    // Reset buttons
    const buttons = ['create-submit-btn', 'join-submit-btn'];
    buttons.forEach(id => {
        const button = document.getElementById(id);
        if (button) {
            button.disabled = false;
        }
    });
    
    // Hide status messages
    document.getElementById('host-status').style.display = 'none';
    document.getElementById('join-status').style.display = 'none';
    
    // Reset game room displays
    const displays = ['player-role', 'player-name-display', 'current-turn', 'turn-status'];
    displays.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = '';
        }
    });
}

// Helper function to update player list with colored bubbles
function updatePlayerList(players) {
    const playersList = document.getElementById('players-list');
    playersList.innerHTML = '';
    players.forEach(player => {
        const li = document.createElement('li');
        const playerBubble = document.createElement('span');
        playerBubble.className = 'player-bubble';
        playerBubble.style.backgroundColor = player.color;
        playerBubble.textContent = player.name + (player.isHost ? ' (Host)' : '');
        li.appendChild(playerBubble);
        playersList.appendChild(li);
    });
}

// Add CSS styles for bubbles
const style = document.createElement('style');
style.textContent = `
    .player-bubble {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        margin: 2px;
        color: #333;
        font-weight: bold;
    }
    
    .word-bubble {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 15px;
        margin: 0 2px;
        color: #333;
    }
    
    #players-list {
        list-style: none;
        padding: 0;
        margin: 10px 0;
    }
    
    #players-list li {
        margin: 5px 0;
    }
    
    #current-sentence {
        line-height: 2;
    }
    
    #game-over {
        text-align: center;
        padding: 20px;
    }
    
    #final-score-list {
        list-style: none;
        padding: 0;
        margin: 20px 0;
    }
    
    #final-score-list li {
        margin: 10px 0;
    }
    
    #final-sentence {
        font-size: 1.2em;
        margin: 20px 0;
        line-height: 1.5;
    }

    #guess-history {
        margin-top: 20px;
        padding: 10px;
        border-top: 1px solid #ccc;
    }

    #guess-history h3 {
        margin-bottom: 10px;
    }

    .guess-list {
        padding: 0;
        margin: 0;
        max-height: 200px;
        overflow-y: auto;
    }

    .guess-entry {
        margin: 5px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .guess-bubble {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 15px;
        color: #333;
    }

    .guess-time {
        font-size: 0.8em;
        color: #666;
    }
    
    .score-text {
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .score-text h4 {
        margin: 0;
        color: #666;
        font-size: 1rem;
    }
    
    .score-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 0.5rem;
    }
`;
document.head.appendChild(style);
 