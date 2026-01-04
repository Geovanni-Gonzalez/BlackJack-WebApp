from app.core.game import BlackJackGame
import traceback

def diagnostic():
    try:
        print("Initializing game...")
        game = BlackJackGame()
        game.start_new_round(num_ai=2)
        
        print(f"Game State: {game.get_state()}")
        
        # Simulate Hit
        print("\nAttempting Player Hit...")
        game.player_hit()
        state = game.get_state()
        print(f"Status: {state['message']}")
        
        # If player stands, trigger AI turns
        print("\nAttempting Player Stand (Trigger AI)...")
        game.player_stand()
        state = game.get_state()
        print(f"Final Message: {state['message']}")
        print(f"Stats: {state['stats']}")
        
    except Exception as e:
        print("\n--- ERROR DETECTED ---")
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic()
