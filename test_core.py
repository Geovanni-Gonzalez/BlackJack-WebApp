from app.core.game import BlackJackGame

def run_console_game():
    game = BlackJackGame()
    game.start_new_round()
    
    print("--- New Game ---")
    print(f"Dealer shows: {game.dealer_hand.cards[1]}") # Show only one card usually, but for debug showing logic
    print(f"Player Hand: {game.player_hand.cards} (Value: {game.player_hand.value})")
    
    # Simple Hit logic for test
    while game.player_hand.value < 15:
        print("Player Hits...")
        game.player_hit()
        print(f"Player Hand: {game.player_hand.cards} (Value: {game.player_hand.value})")
        if game.player_hand.busted:
            print("PLAYER BUSTED!")
            break
            
    if not game.player_hand.busted:
        print("Player Stands.")
        game.player_stand()
        
    print(f"Final Message: {game.message}")
    print(f"Dealer Hand: {game.dealer_hand.cards} (Value: {game.dealer_hand.value})")
    print(f"Winner: {game.winner}")

if __name__ == "__main__":
    run_console_game()
