import random

SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = VALUES[rank]

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    def to_dict(self):
        return {'rank': self.rank, 'suit': self.suit, 'value': self.value}

class Deck:
    def __init__(self, num_decks=1):
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS] * num_decks
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            return None # Or raise EmptyDeckException
        return self.cards.pop()
    
    def remaining(self):
        return len(self.cards)
