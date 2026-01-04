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
            # Clone State (simplified)
            # We create a new game instance to avoid messing up the real game
            from app.core.game import BlackJackGame
            sim_game = BlackJackGame()
            
            # Setup specific hands
            # Ideally we'd remove cards from sim_game.deck that are already seen.
            # For this basic version, we assume a full 6-deck shoe for every sim (Monte Carlo approximation).
            
            sim_game.player_hand = copy.deepcopy(current_player_hand)
            sim_game.dealer_hand.cards = [current_dealer_hand_card] # We only know one dealer card
            sim_game.dealer_hand.calculate()
            
            # Action: Hit
            sim_game.player_hit()
            
            if sim_game.player_hand.busted:
                # Loss
                continue
                
            # After Hit, play out Dealer
            # (Assuming Player stands after this hit, or we could continue player turn)
            # Let's assume Player Stands to see if this *state* is good.
            sim_game.dealer_turn()
            
            if sim_game.winner == 1:
                wins += 1
            elif sim_game.winner == 0:
                draws += 0.5 # Count draw as half win? Or just track raw wins.
                
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
            sim_game.player_hand = copy.deepcopy(current_player_hand)
            sim_game.dealer_hand.cards = [current_dealer_hand_card]
            sim_game.dealer_hand.calculate()
            
            # Action: Stand (Immediate Dealer Turn)
            sim_game.dealer_turn()
            
            if sim_game.winner == 1:
                wins += 1
            elif sim_game.winner == 0:
                draws += 0.5
                
        return (wins + draws) / self.num_simulations
