import argparse
from concurrent.futures import ProcessPoolExecutor
from ai_player import run_ai_player

def run_multiple_ai_players(game_code: str, num_players: int = 4):
    """
    Spin up multiple AI players in separate processes.
    
    Args:
        game_code (str): The game code to join
        num_players (int): Number of AI players to create (default: 4)
    """
    ai_names = [f"AI_Player_{i+1}" for i in range(num_players)]
    
    # Start AI players in separate processes
    with ProcessPoolExecutor(max_workers=num_players) as executor:
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run AI players for the word guessing game')
    parser.add_argument('-n', '--num_players', type=int, default=4,
                       help='Number of AI players to create (default: 4)')
    args = parser.parse_args()

    game_code = input("Enter game code: ")
    run_multiple_ai_players(game_code, args.num_players) 