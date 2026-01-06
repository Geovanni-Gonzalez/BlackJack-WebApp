from app.core.game import BlackJackGame

def run_console_game():
    game = BlackJackGame()
    game.start_new_round()
    
    # Place bet and confirm to deal cards
    game.players[0].place_bet(100)
    game.confirm_bets()
    
    print("--- New Game ---")
    print(f"Dealer shows: {game.dealer_hand.cards[1]}") # Show only one card usually, but for debug showing logic
    human_player = game.players[0]
    print(f"Player Hand: {human_player.cards} (Value: {human_player.value})")
    
    # Simple Hit logic for test
    while human_player.value < 15:
        print("Player Hits...")
        game.player_hit()
        print(f"Player Hand: {human_player.cards} (Value: {human_player.value})")
        if human_player.busted:
            print("PLAYER BUSTED!")
            break
            
    if not human_player.busted:
        print("Player Stands.")
        game.player_stand()
        
    print(f"Final Message: {game.message}")
    print(f"Dealer Hand: {game.dealer_hand.cards} (Value: {game.dealer_hand.value})")
    print(f"Stats: {game.stats}")

if __name__ == "__main__":
    run_console_game()
