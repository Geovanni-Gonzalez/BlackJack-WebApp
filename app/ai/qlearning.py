import random
import os
import json
from app.core.rules import determine_winner

class QLearningAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1, model_path='q_table.json'):
        """
        alpha: Learning Rate
        gamma: Discount Factor
        epsilon: Exploration Rate
        """
        self.q_table = {} # Key: (player_sum, dealer_card, usable_ace), Value: [q_stand, q_hit]
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.training_stats = []
        self.model_path = model_path
        self.load()

    def save(self):
        """Saves the Q-table to a JSON file."""
        # Convert tuple keys to strings for JSON
        serializable_q = {str(k): v for k, v in self.q_table.items()}
        with open(self.model_path, 'w') as f:
            json.dump(serializable_q, f)

    def load(self):
        """Loads the Q-table from a JSON file."""
        if os.path.exists(self.model_path):
            try:
                import ast
                with open(self.model_path, 'r') as f:
                    data = json.load(f)
                    # Use literal_eval for safer key conversion
                    self.q_table = {ast.literal_eval(k): v for k, v in data.items() if k != "test_state"}
            except Exception as e:
                print(f"Error loading Q-table: {e}")
                self.q_table = {}

    def get_state(self, game, player_hand):
        """
        Extracts state from game object.
        State: (Player Sum, Dealer Show Card Value, True Count Bucket)
        """
        player_val = player_hand.value
        # Use dealer's visible card (usually index 1)
        dealer_card_val = 0
        if len(game.dealer_hand.cards) >= 1:
            # If 2 cards, use index 1 (standard up-card), else index 0
            idx = 1 if len(game.dealer_hand.cards) >= 2 else 0
            dealer_card_val = game.dealer_hand.cards[idx].value
        
        # True Count Bucket
        running_count = game.counter.running_count
        if running_count <= -2:
            count_state = -1
        elif running_count >= 2:
            count_state = 1
        else:
            count_state = 0
            
        return (player_val, dealer_card_val, count_state)

    def get_q_values(self, state):
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0] # [Stand, Hit]
        return self.q_table[state]

    def choose_action(self, state):
        """
        Returns 0 (Stand) or 1 (Hit)
        """
        if random.random() < self.epsilon:
            return random.choice([0, 1])
        
        q_vals = self.get_q_values(state)
        # Return index of max value
        if q_vals[0] >= q_vals[1]:
            return 0
        else:
            return 1

    def learn(self, state, action, reward, next_state, done):
        q_vals = self.get_q_values(state)
        old_val = q_vals[action]
        
        if done:
            target = reward
        else:
            next_q = self.get_q_values(next_state)
            target = reward + self.gamma * max(next_q)
            
        # Update
        q_vals[action] = old_val + self.alpha * (target - old_val)
        
        if done:
            self.save()

    def train(self, num_episodes=10000):
        wins = 0
        losses = 0
        draws = 0
        
        from app.core.game import BlackJackGame
        
        for i in range(num_episodes):
            game = BlackJackGame()
            game.start_new_round(num_ai=0) # Train solo for speed
            
            human_player = game.players[0]
            state = self.get_state(game, human_player)
            
            while not game.game_over:
                action = self.choose_action(state)
                
                # Execute Action
                if action == 1: # Hit
                    game.player_hit()
                    reward = 0
                    if human_player.busted:
                        reward = -1
                        done = True
                    else:
                        done = False
                else: # Stand
                    game.player_stand()
                    done = True
                    # In new game engine, we check result manually for reward
                    res = determine_winner(human_player.value, game.dealer_hand.value)
                    if res == 1: reward = 1
                    elif res == -1: reward = -1
                    else: reward = 0
                
                next_state = self.get_state(game, human_player)
                self.learn(state, action, reward, next_state, done)
                state = next_state
                
                if done:
                    res = determine_winner(human_player.value, game.dealer_hand.value)
                    if res == 1: wins += 1
                    elif res == -1: losses += 1
                    else: draws += 1
            
            # Log progress every 1000
            if (i+1) % 1000 == 0:
                win_rate = wins / (i+1)
                self.training_stats.append((i+1, win_rate))
                # print(f"Episode {i+1}: Win Rate {win_rate:.1%}")
                
        return wins, losses, draws

    def generate_strategy_heatmap(self):
        """
        Generates a strategy heatmap showing optimal actions for each state.
        Returns a 2D matrix: rows = player sum (4-21), cols = dealer card (2-11)
        Values: 0 = Stand, 1 = Hit, 2 = Equal (no clear preference)
        """
        heatmap = []
        
        # Player sums from 4 to 21
        for player_sum in range(4, 22):
            row = []
            # Dealer cards from 2 to 11 (Ace)
            for dealer_card in range(2, 12):
                # Check all count states and average
                actions = []
                for count_state in [-1, 0, 1]:
                    state = (player_sum, dealer_card, count_state)
                    q_vals = self.get_q_values(state)
                    
                    # Determine optimal action
                    if abs(q_vals[0] - q_vals[1]) < 0.01:  # Nearly equal
                        actions.append(2)
                    elif q_vals[0] > q_vals[1]:  # Stand is better
                        actions.append(0)
                    else:  # Hit is better
                        actions.append(1)
                
                # Most common action across count states
                action = max(set(actions), key=actions.count)
                row.append(action)
            
            heatmap.append(row)
        
        return heatmap
    
    def get_strategy_details(self, player_sum, dealer_card):
        """
        Get detailed Q-values for a specific state across all count states.
        Returns dict with analysis for each count state.
        """
        details = {}
        
        for count_state in [-1, 0, 1]:
            state = (player_sum, dealer_card, count_state)
            q_vals = self.get_q_values(state)
            
            count_label = "Negative" if count_state == -1 else ("Neutral" if count_state == 0 else "Positive")
            
            details[count_label] = {
                'q_stand': round(q_vals[0], 3),
                'q_hit': round(q_vals[1], 3),
                'optimal_action': 'Stand' if q_vals[0] >= q_vals[1] else 'Hit',
                'confidence': round(abs(q_vals[0] - q_vals[1]), 3)
            }
        
        return details
    
    def compare_with_basic_strategy(self):
        """
        Compare Q-Learning strategy with basic Blackjack strategy.
        Returns accuracy percentage and differences.
        """
        # Basic strategy rules (simplified)
        basic_strategy = {
            # (player_sum, dealer_card): action (0=Stand, 1=Hit)
        }
        
        # Hard totals basic strategy
        for player_sum in range(4, 22):
            for dealer_card in range(2, 12):
                # Simplified basic strategy
                if player_sum >= 17:
                    basic_strategy[(player_sum, dealer_card)] = 0  # Stand
                elif player_sum <= 11:
                    basic_strategy[(player_sum, dealer_card)] = 1  # Hit
                elif player_sum >= 13 and dealer_card <= 6:
                    basic_strategy[(player_sum, dealer_card)] = 0  # Stand
                elif player_sum == 12 and 4 <= dealer_card <= 6:
                    basic_strategy[(player_sum, dealer_card)] = 0  # Stand
                else:
                    basic_strategy[(player_sum, dealer_card)] = 1  # Hit
        
        # Compare Q-Learning with basic strategy
        matches = 0
        total = 0
        differences = []
        
        for (player_sum, dealer_card), basic_action in basic_strategy.items():
            state = (player_sum, dealer_card, 0)  # Use neutral count
            q_vals = self.get_q_values(state)
            q_action = 0 if q_vals[0] >= q_vals[1] else 1
            
            total += 1
            if q_action == basic_action:
                matches += 1
            else:
                differences.append({
                    'player_sum': player_sum,
                    'dealer_card': dealer_card,
                    'basic': 'Stand' if basic_action == 0 else 'Hit',
                    'q_learning': 'Stand' if q_action == 0 else 'Hit',
                    'q_values': [round(q_vals[0], 3), round(q_vals[1], 3)]
                })
        
        accuracy = (matches / total * 100) if total > 0 else 0
        
        return {
            'accuracy': round(accuracy, 2),
            'matches': matches,
            'total': total,
            'differences': differences[:10]  # Top 10 differences
        }
