def calculate_hand_value(cards):
    """
    Calculates the value of a hand, handling Aces.
    Returns best value <= 21 if possible, else the lowest bust value.
    """
    value = sum(card.value for card in cards)
    aces = sum(1 for card in cards if card.rank == 'A')

    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    
    return value

def is_blackjack(cards):
    return len(cards) == 2 and calculate_hand_value(cards) == 21

def is_bust(value):
    return value > 21

def determine_winner(player_value, dealer_value):
    """
    Returns: 1 if Player wins, -1 if Dealer wins, 0 if Draw
    """
    if player_value > 21:
        return -1
    if dealer_value > 21:
        return 1
    
    if player_value > dealer_value:
        return 1
    elif dealer_value > player_value:
        return -1
    else:
        return 0
