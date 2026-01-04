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
                with open(self.model_path, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to tuples using eval
                    self.q_table = {eval(k): v for k, v in data.items()}
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
