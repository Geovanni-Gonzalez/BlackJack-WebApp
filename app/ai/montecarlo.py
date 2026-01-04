import random
import copy
from app.core.rules import determine_winner

class MonteCarloSimulator:
    def __init__(self, num_simulations=1000):
        self.num_simulations = num_simulations

    def simulate_hit_win_rate(self, current_player_hand, current_dealer_hand_card, deck_state=None):
        """
        Simulates hitting from the current state 'num_simulations' times.
        Returns the probability of winning (or not losing) if hitting.
        
        Note: deck_state could be used for card counting/exact probabilities.
        For now, we assume an infinite deck or reshuffled deck approximation if deck_state is complex to clone.
        To be accurate, we should clone the game state perfectly.
        """
        wins = 0
        draws = 0
        
        # We need to simulate the rest of the game after hitting *once*.
        # Strategy for simulation: 
        # 1. Hit once (this is the action we are evaluating).
        # 2. If bust, loss.
        # 3. If not bust, play out the rest of the hand (e.g., random moves or basic strategy).
        #    For pure Monte Carlo evaluation of "Hit vs Stand", we usually evaluate the *immediate* action 
        #    and then assume optimal or random play. 
        #    Let's assume the player Stands after this Hit for simplicity effectively evaluating "Hit then Stand",
        #    or we can play a simple strategy like "Hit until 17".
        
        for _ in range(self.num_simulations):
            from app.core.game import BlackJackGame
            sim_game = BlackJackGame()
            sim_game.start_new_round(num_ai=0) # Simple 1v1 for simulation
            
            # Setup specific state
            sim_game.players[0] = copy.deepcopy(current_player_hand)
            sim_game.dealer_hand.cards = [current_dealer_hand_card]
            sim_game.dealer_hand.calculate()
            
            # Action: Hit
            sim_game.player_hit()
            
            player = sim_game.players[0]
            if player.busted: continue
                
            sim_game.dealer_turn()
            
            # Use direct determine_winner since winner attr is gone
            result = determine_winner(player.value, sim_game.dealer_hand.value)
            if result == 1:
                wins += 1
            elif result == 0:
                draws += 0.5
                
        return (wins + draws) / self.num_simulations

    def simulate_stand_win_rate(self, current_player_hand, current_dealer_hand_card):
        """
        Simulates standing from the current state.
        """
        wins = 0
        draws = 0
        
        for _ in range(self.num_simulations):
            from app.core.game import BlackJackGame
            sim_game = BlackJackGame()
            sim_game.start_new_round(num_ai=0)
            
            sim_game.players[0] = copy.deepcopy(current_player_hand)
            sim_game.dealer_hand.cards = [current_dealer_hand_card]
            sim_game.dealer_hand.calculate()
            
            # Action: Stand (Immediate Dealer Turn)
            sim_game.dealer_turn()
            
            player = sim_game.players[0]
            result = determine_winner(player.value, sim_game.dealer_hand.value)
            if result == 1:
                wins += 1
            elif result == 0:
                draws += 0.5
                
        return (wins + draws) / self.num_simulations
