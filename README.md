# Polycephaly - Collaborative Word Game

A real-time multiplayer web game where players collaboratively construct sentences while one player tries to guess the subject. Built with Flask, WebSocket, and vanilla JavaScript.

## Features

- Real-time multiplayer gameplay using WebSockets
- Clean and responsive user interface
- Turn-based word addition system
- Scoring system for correct guesses
- Support for multiple simultaneous games
- Mobile-friendly design

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser with WebSocket support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/polycephaly.git
cd polycephaly
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

1. Start the server:
```bash
python server.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## How to Play

1. **Creating a Game**
   - Click "Create Game" on the landing page
   - Enter your name
   - Share the generated game code with other players

2. **Joining a Game**
   - Click "Join Game" on the landing page
   - Enter the game code and your name

3. **Gameplay**
   - The host enters a subject for others to describe
   - Players take turns adding one word at a time to build a sentence
   - The guesser tries to figure out the subject based on the sentence
   - Points are awarded for correct guesses

## Deployment

### Local Network

To make the game accessible on your local network:

1. Modify the server.py host parameter:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

2. Access the game using your computer's local IP address:
```
http://YOUR_LOCAL_IP:5000
```

### Production Deployment

For production deployment, consider:

1. Using a production-grade WSGI server (e.g., Gunicorn)
2. Setting up a reverse proxy (e.g., Nginx)
3. Implementing proper security measures
4. Using environment variables for configuration

Example production setup with Gunicorn:

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Run with Gunicorn:
```bash
gunicorn --worker-class eventlet -w 1 server:app
```

## Project Structure

```
polycephaly/
├── server.py           # Flask server and game logic
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Game styling
│   └── js/
│       └── main.js    # Client-side game logic
├── templates/
│   └── index.html     # Game interface
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask-SocketIO for real-time communication
- Modern web technologies (HTML5, CSS3, ES6+)
- The open-source community 