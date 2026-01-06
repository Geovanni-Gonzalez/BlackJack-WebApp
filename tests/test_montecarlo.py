from app.core.game import Hand
from app.core.cards import Card
from app.ai.montecarlo import MonteCarloSimulator

def test_simulation():
    print("--- Monte Carlo Simulation Test ---")
    mc = MonteCarloSimulator(num_simulations=100) # Fast test
    
    # Scene 1: Player has 20 vs Dealer 5. Should Stand.
    player_hand = Hand()
    player_hand.add_card(Card('10', 'Hearts'))
    player_hand.add_card(Card('10', 'Spades')) # 20
    
    dealer_card = Card('5', 'Clubs')
    
    prob_hit = mc.simulate_hit_win_rate(player_hand, dealer_card)
    prob_stand = mc.simulate_stand_win_rate(player_hand, dealer_card)
    
    print(f"Scenario: Player 20 vs Dealer 5")
    print(f"Win Probability if HIT: {prob_hit:.2%}")
    print(f"Win Probability if STAND: {prob_stand:.2%}")
    
    if prob_stand > prob_hit:
        print("RESULT: CORRECT (Stand > Hit)")
    else:
        print("RESULT: FAILURE (Logic or Bad Luck?)")

    # Scene 2: Player has 10 vs Dealer 6. Should Hit.
    print("\n")
    player_hand_2 = Hand()
    player_hand_2.add_card(Card('5', 'Hearts'))
    player_hand_2.add_card(Card('5', 'Spades')) # 10
    
    prob_hit_2 = mc.simulate_hit_win_rate(player_hand_2, dealer_card)
    prob_stand_2 = mc.simulate_stand_win_rate(player_hand_2, dealer_card)
    
    print(f"Scenario: Player 10 vs Dealer 5")
    print(f"Win Probability if HIT: {prob_hit_2:.2%}")
    print(f"Win Probability if STAND: {prob_stand_2:.2%}")
    
    if prob_hit_2 > prob_stand_2:
        print("RESULT: CORRECT (Hit > Stand)")
    else:
        print("RESULT: FAILURE")

if __name__ == "__main__":
    test_simulation()
