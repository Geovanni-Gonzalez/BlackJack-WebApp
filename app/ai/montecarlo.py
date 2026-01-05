import random
import copy
from app.core.rules import determine_winner
from functools import lru_cache

class MonteCarloSimulator:
    def __init__(self, num_simulations=500):
        self.num_simulations = num_simulations

    def _is_soft(self, hand):
        """Returns True if the hand has a usable Ace (counted as 11)."""
        # Card.value returns 11 for Ace usually.
        # Check if current calculated value uses an Ace as 11.
        # Minimal value (all aces as 1) can be calculated.
        # If current value > min_value + 5 (essentially +10), it's soft.
        
        # Simplified check based on common patterns:
        if hand.value <= 11: return False # Cannot be soft if <= 11? e.g. A,A -> 12 (Soft? One is 11).
        # Actually value 12 (A,A) is soft. min=2. value=12. diff=10.
        
        # We can implement a robust check logic if we had access to Card objects properties
        # But assuming inputs are Hand objects:
        raw_ace_sum = sum(c.value for c in hand.cards)
        # If raw sum equals value and we have an ace, it *might* be soft (A+8=19). 
        # If raw sum > value, we reduced some aces. If we reduced ALL, it's hard.
        
        # Better Proxy: Pass is_soft explicitly or rely on value logic.
        # Let's recreate the hand logic:
        # A soft hand is one where at least one Ace is counted as 11.
        # If value <= 11, it can only be soft if A+A=12.
        # If value >= 12, it is soft if (value - 10) >= sum(1s for Aces).
        
        # For simplicity in this optimization task, let's look at the result:
        # If standard Blackjack rules:
        # Soft 13 (A,2) -> 3 or 13. Value 13.
        # Hard 13 (10,3) -> 13. Value 13.
        # Difference? Hitting Soft 13 can't bust. Hitting Hard 13 can.
        
        # HEURISTIC: boolean
        # If we can hit and NOT bust with a 10, it was NOT pure hard? No.
        
        # Correct logic:
        aces = sum(1 for c in hand.cards if c.rank == 'A')
        if aces == 0: return False
        
        # Calculate min value (all aces = 1)
        non_aces_val = sum(c.value for c in hand.cards if c.rank != 'A')
        min_val = non_aces_val + aces
        
        # If actual value is > min_val, it means at least one ace is 11.
        return hand.value > min_val

    def simulate_hit_win_rate(self, current_player_hand, current_dealer_hand_card, deck_state=None):
        return self._cached_simulate_hit(
            current_player_hand.value,
            current_dealer_hand_card.value,
            self._is_soft(current_player_hand)
        )

    def simulate_stand_win_rate(self, current_player_hand, current_dealer_hand_card):
        return self._cached_simulate_stand(
            current_player_hand.value,
            current_dealer_hand_card.value,
            self._is_soft(current_player_hand)
        )

    @lru_cache(maxsize=2048)
    def _cached_simulate_hit(self, player_val, dealer_val, is_soft):
        """Cached worker for Hit"""
        wins = 0
        draws = 0
        
        for _ in range(self.num_simulations):
            from app.core.game import BlackJackGame
            from app.core.cards import Card
            
            sim_game = BlackJackGame()
            sim_game.start_new_round(num_ai=0)
            
            # Reconstruct Dealer
            # If dealer_val is 11, it's an Ace
            rank = 'A' if dealer_val == 11 else str(dealer_val) if dealer_val != 10 else 'K'
            # Card(rank, suit) - Correct signature
            sim_game.dealer_hand.cards = [Card(rank, 'H')]
            sim_game.dealer_hand.calculate()
            
            # Reconstruct Player
            p_hand = sim_game.players[0]
            p_hand.cards = []
            
            if is_soft:
                # Soft X: e.g. Soft 18 (A, 7). val=18. needs 11+7. card=7 -> val-11
                rem = player_val - 11
                p_hand.cards.append(Card('A', 'S'))
                if rem > 0:
                    r_rank = str(rem) if rem < 10 else 'K'
                    p_hand.cards.append(Card(r_rank, 'S'))
            else:
                # Hard X: e.g. 15. (10, 5)
                # To be generic, split roughly in half to simulate 2 cards
                c1 = player_val // 2
                c2 = player_val - c1
                # Handle invalid card values (e.g. 1)
                if c1 < 2: c1=2 # Should not happen for Hard >= 4
                
                # Helper to make card
                def make_card(v):
                    r = str(v) if v < 10 else 'K'
                    return Card(r, 'C')
                    
                p_hand.cards.append(make_card(c1))
                p_hand.cards.append(make_card(c2))
                
            p_hand.calculate()
            
            # Action: Hit
            sim_game.player_hit()
            
            player = sim_game.players[0]
            if player.busted:
                continue # Loss (wins not incremented)
                
            sim_game.dealer_turn()
            
            result = determine_winner(player.value, sim_game.dealer_hand.value)
            if result == 1:
                wins += 1
            elif result == 0:
                draws += 0.5
                
        return (wins + draws) / self.num_simulations

    @lru_cache(maxsize=2048)
    def _cached_simulate_stand(self, player_val, dealer_val, is_soft):
        """Cached worker for Stand"""
        wins = 0
        draws = 0
        
        for _ in range(self.num_simulations):
            from app.core.game import BlackJackGame
            from app.core.cards import Card
            
            sim_game = BlackJackGame()
            sim_game.start_new_round(num_ai=0)
            
            # Reconstruct Dealer
            rank = 'A' if dealer_val == 11 else str(dealer_val) if dealer_val != 10 else 'K'
            sim_game.dealer_hand.cards = [Card(rank, 'H')]
            sim_game.dealer_hand.calculate()
            
            # Reconstruct Player
            p_hand = sim_game.players[0]
            p_hand.cards = []
            
            if is_soft:
                rem = player_val - 11
                p_hand.cards.append(Card('A', 'S'))
                if rem > 0:
                    r_rank = str(rem) if rem < 10 else 'K'
                    p_hand.cards.append(Card(r_rank, 'S'))
            else:
                c1 = player_val // 2
                c2 = player_val - c1
                if c1 < 2: c1=2
                
                def make_card(v):
                    r = str(v) if v < 10 else 'K'
                    return Card(r, 'C')
                p_hand.cards.append(make_card(c1))
                p_hand.cards.append(make_card(c2))
            
            p_hand.calculate()
            
            # Action: Stand -> Dealer plays
            sim_game.dealer_turn()
            
            player = sim_game.players[0]
            result = determine_winner(player.value, sim_game.dealer_hand.value)
            if result == 1:
                wins += 1
            elif result == 0:
                draws += 0.5
                
        return (wins + draws) / self.num_simulations
