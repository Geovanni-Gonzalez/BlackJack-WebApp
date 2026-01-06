from app.ai.qlearning import QLearningAgent

def test_qlearning():
    print("--- Q-Learning Training Test ---")
    agent = QLearningAgent(alpha=0.1, gamma=0.9, epsilon=0.1)
    
    print("Training for 2000 episodes...")
    wins, losses, draws = agent.train(num_episodes=2000)
    
    total = wins + losses + draws
    win_rate = wins / total
    print(f"Training Complete. Total Games: {total}")
    print(f"Wins: {wins} ({win_rate:.2%})")
    print(f"Losses: {losses} ({(losses/total):.2%})")
    print(f"Draws: {draws} ({(draws/total):.2%})")
    
    # Inspect Q-Table for a common state: Player 20, Dealer 6, Neutral Count (0)
    # Should strongly prefer Stand (0) over Hit (1)
    state_20_vs_6 = (20, 6, 0)
    q_vals = agent.get_q_values(state_20_vs_6)
    print(f"\nState {state_20_vs_6} (Player 20 vs Dealer 6, Neutral Count): {q_vals}")
    
    if q_vals[0] > q_vals[1]:
        print("RESULT: CORRECT (Agent learned to Stand on 20)")
    else:
        print("RESULT: UNCERTAIN (Agent prefers Hit? Might need more training or bad luck)")
    
    # Check populated size
    print(f"\nQ-Table Size (States Visited): {len(agent.q_table)}")

if __name__ == "__main__":
    test_qlearning()
