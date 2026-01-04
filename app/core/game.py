from .cards import Deck
from .rules import calculate_hand_value, is_bust, determine_winner
from app.ai.counter import CardCounter

class Hand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.busted = False

    def add_card(self, card):
        self.cards.append(card)
        self.calculate()

    def calculate(self):
        self.value = calculate_hand_value(self.cards)
        self.busted = is_bust(self.value)
    
    def to_dict(self):
        return {
            'cards': [c.to_dict() for c in self.cards],
            'value': self.value,
            'busted': self.busted
        }

class BlackJackGame:
    def __init__(self, num_decks=6):
        self.deck = Deck(num_decks=num_decks)
        self.counter = CardCounter()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.game_over = False
        self.winner = None # 1: Player, -1: Dealer, 0: Draw
        self.message = ""

    def start_new_round(self):
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.game_over = False
        self.winner = None
        self.message = ""
        
        if self.deck.remaining() < 20: # Reshuffle if low
            self.deck = Deck(num_decks=6)
            self.counter.reset()

        # Initial Deal
        self._deal_card_to(self.player_hand)
        self._deal_card_to(self.dealer_hand)
        self._deal_card_to(self.player_hand)
        self._deal_card_to(self.dealer_hand)
    
    def _deal_card_to(self, hand):
        card = self.deck.deal()
        self.counter.update(card)
        hand.add_card(card)

    def player_hit(self):
        if self.game_over: return
        
        self._deal_card_to(self.player_hand)
        
        if self.player_hand.busted:
            self.game_over = True
            self.winner = -1
            self.message = "Player Busted!"

    def player_stand(self):
        if self.game_over: return
        self.dealer_turn()

    def dealer_turn(self):
        # Dealer hits on soft 17 is standard, sticking to simple "Hit < 17" for now
        while self.dealer_hand.value < 17:
            self._deal_card_to(self.dealer_hand)
        
        self.game_over = True
        self.winner = determine_winner(self.player_hand.value, self.dealer_hand.value)
        
        if self.winner == 1: self.message = "Player Wins!"
        elif self.winner == -1: self.message = "Dealer Wins!"
        else: self.message = "Draw!"
        
    def get_state(self):
        return {
            'player_hand': self.player_hand.to_dict(),
            # In real game, dealer 2nd card is hidden until stand. 
            # For simplicity/AI training, we might expose it or hide it. 
            # Web UI should hide it. AI might assume probabilities.
            'dealer_hand': self.dealer_hand.to_dict(), 
            'count': self.counter.running_count,
            'suggestion': self.counter.get_suggestion(),
            'game_over': self.game_over,
            'winner': self.winner,
            'message': self.message
        }
