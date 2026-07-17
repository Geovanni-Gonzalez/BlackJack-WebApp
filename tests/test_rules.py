from app.core.cards import Card
from app.core.rules import calculate_hand_value, is_blackjack, is_bust, determine_winner


def test_ace_counts_as_eleven_when_safe():
    assert calculate_hand_value([Card('A', 'Hearts'), Card('7', 'Spades')]) == 18


def test_ace_downgrades_to_one_to_avoid_bust():
    hand = [Card('A', 'Hearts'), Card('9', 'Spades'), Card('5', 'Clubs')]
    assert calculate_hand_value(hand) == 15


def test_multiple_aces():
    assert calculate_hand_value([Card('A', 'Hearts'), Card('A', 'Spades')]) == 12


def test_blackjack_detection():
    assert is_blackjack([Card('A', 'Hearts'), Card('K', 'Spades')]) is True
    assert is_blackjack([Card('7', 'Hearts'), Card('7', 'Spades')]) is False


def test_bust_boundary():
    assert is_bust(22) is True
    assert is_bust(21) is False


def test_determine_winner():
    assert determine_winner(20, 18) == 1
    assert determine_winner(18, 20) == -1
    assert determine_winner(19, 19) == 0
    assert determine_winner(22, 18) == -1
    assert determine_winner(18, 25) == 1
