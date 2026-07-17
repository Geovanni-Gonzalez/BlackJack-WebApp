from app.core.cards import Card
from app.ai.counter import CardCounter


def test_hi_lo_running_count():
    counter = CardCounter()
    for r in ['2', '5', 'K', '10', '7', 'A']:
        counter.update(Card(r, 'Hearts'))
    assert counter.running_count == -1
    assert counter.total_cards_dealt == 6


def test_reset():
    counter = CardCounter()
    counter.update(Card('2', 'Hearts'))
    counter.reset()
    assert counter.running_count == 0
    assert counter.total_cards_dealt == 0


def test_true_count():
    counter = CardCounter()
    counter.running_count = 6
    assert counter.get_true_count(3) == 2


def test_suggestion_thresholds():
    counter = CardCounter()
    counter.running_count = 5
    assert 'High' in counter.get_suggestion() or 'Aggressive' in counter.get_suggestion()
    counter.running_count = -5
    assert 'Low' in counter.get_suggestion() or 'Conservative' in counter.get_suggestion()
