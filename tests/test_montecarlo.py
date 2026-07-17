from app.core.game import Hand
from app.core.cards import Card, Deck
from app.ai.montecarlo import MonteCarloSimulator


def _hand(*ranks):
    h = Hand()
    for r in ranks:
        h.add_card(Card(r, 'Hearts'))
    return h


def test_probabilities_are_in_range():
    mc = MonteCarloSimulator(num_simulations=200)
    hand = _hand('10', '6')
    dealer = Card('10', 'Clubs')
    assert 0.0 <= mc.simulate_hit_win_rate(hand, dealer) <= 1.0
    assert 0.0 <= mc.simulate_stand_win_rate(hand, dealer) <= 1.0


def test_standing_on_20_beats_hitting():
    mc = MonteCarloSimulator(num_simulations=400)
    hand = _hand('10', '10')
    dealer = Card('5', 'Clubs')
    assert mc.simulate_stand_win_rate(hand, dealer) > mc.simulate_hit_win_rate(hand, dealer)


def test_hitting_low_hand_beats_standing():
    mc = MonteCarloSimulator(num_simulations=400)
    hand = _hand('5', '2')
    dealer = Card('10', 'Clubs')
    assert mc.simulate_hit_win_rate(hand, dealer) >= mc.simulate_stand_win_rate(hand, dealer)


def test_deck_argument_is_respected():
    mc = MonteCarloSimulator(num_simulations=100)
    hand = _hand('9', '7')
    dealer = Card('6', 'Clubs')
    assert 0.0 <= mc.simulate_hit_win_rate(hand, dealer, deck=Deck(num_decks=6)) <= 1.0
