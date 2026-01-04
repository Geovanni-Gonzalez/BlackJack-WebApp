from app.core.cards import Card
from app.ai.counter import CardCounter

def test_counter():
    print("--- Card Counter Test (Hi-Lo) ---")
    counter = CardCounter()
    
    # 2, 3, 4, 5, 6 -> +1 each
    # 7, 8, 9 -> 0
    # 10, J, Q, K, A -> -1 each
    
    cards = [
        Card('2', 'Hearts'), # +1
        Card('5', 'Clubs'),  # +1 (Total +2)
        Card('K', 'Spades'), # -1 (Total +1)
        Card('10', 'Diamonds'), # -1 (Total 0)
        Card('7', 'Hearts'), # 0 (Total 0)
        Card('A', 'Clubs')   # -1 (Total -1)
    ]
    
    for card in cards:
        counter.update(card)
        print(f"Card: {card}, Running Count: {counter.running_count}")
        
    print(f"Final Count: {counter.running_count}")
    
    if counter.running_count == -1:
        print("RESULT: CORRECT")
    else:
        print("RESULT: FAILURE")

if __name__ == "__main__":
    test_counter()
