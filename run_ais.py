import argparse
import asyncio
from ai_player import run_ai_player

async def run_multiple_ai_players(game_code: str, num_players: int = 4):
    """
    Spin up multiple AI players concurrently using asyncio.
    
    Args:
        game_code (str): The game code to join
        num_players (int): Number of AI players to create (default: 4)
    """
    ai_names = [f"AI_Player_{i+1}" for i in range(num_players)]
    
    # Create tasks for all AI players
    tasks = [
        asyncio.create_task(run_ai_player(name, game_code))
        for name in ai_names
    ]
    
    try:
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Shutting down AI players...")
        # Cancel all running tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for tasks to be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)

def main():
    parser = argparse.ArgumentParser(description='Run AI players for the word guessing game')
    parser.add_argument('-n', '--num_players', type=int, default=4,
                       help='Number of AI players to create (default: 4)')
    args = parser.parse_args()

    game_code = input("Enter game code: ")
    
    # Run the async main function
    try:
        asyncio.run(run_multiple_ai_players(game_code, args.num_players))
    except KeyboardInterrupt:
        print("\nShutdown complete.")

if __name__ == '__main__':
    main() 