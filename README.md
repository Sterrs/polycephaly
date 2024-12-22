# Polycephaly

A multiplayer word guessing game where players compete to find a target word by making guesses and receiving feedback. The game combines elements of classic word games with a competitive twist.

## Game Rules

1. Players join a game session and take turns making guesses
2. Each guess must be a valid word from the game's dictionary
3. After each guess, players receive feedback:
   - Green: Letter is in the correct position
   - Yellow: Letter is in the word but wrong position
   - Gray: Letter is not in the word
4. The first player to correctly guess the target word wins
5. Players can see each other's guesses and their feedback

## Technical Details

- Built with Python (Flask) backend and JavaScript frontend
- Real-time updates using Socket.IO
- Word validation against a curated dictionary
- Secure game state management
- Responsive web interface

## Setup

1. Clone the repository
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `config/config.json` file with your configuration
5. Run the server:
   ```bash
   python server.py
   ```

## License

This project is licensed under the AGPL-3.0 License - see the LICENSE file for details.