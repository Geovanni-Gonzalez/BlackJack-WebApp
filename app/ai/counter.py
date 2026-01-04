from app.core.cards import Card

class CardCounter:
    def __init__(self):
        self.running_count = 0
        self.total_cards_dealt = 0
    
    def reset(self):
        self.running_count = 0
        self.total_cards_dealt = 0
        
    def update(self, card):
        """
        Updates count based on Hi-Lo System:
        2-6: +1
        7-9: 0
        10-A: -1
        """
        if card.value >= 2 and card.value <= 6:
            self.running_count += 1
        elif card.value >= 10: # 10, J, Q, K, A (A is 11)
            self.running_count -= 1
        # 7, 8, 9 are neutral (0)
        
        self.total_cards_dealt += 1
        
    def get_true_count(self, decks_remaining):
        if decks_remaining < 0.5: return self.running_count # Avoid division by zero/small
        return self.running_count / decks_remaining

    def get_suggestion(self):
        # Basic derivation: High count = Bet More / Stand more?
        # Actually in blackjack, high count means more 10s/As remaining.
        # Player gets more blackjacks (3:2 payout), dealer busts more on stiff hands.
        if self.running_count > 2:
            return "Bet High / Aggressive"
        elif self.running_count < -2:
            return "Bet Low / Conservative"
        return "Neutral"
