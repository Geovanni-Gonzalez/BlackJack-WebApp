"""Monte Carlo win-probability estimation for Blackjack.

The simulator plays out many random completions of the current hand and reports
the fraction of favourable outcomes (a draw counts as half a win).

Fidelity notes (previous version approximated the player's hand as ``value//2``
and always used a fresh single-card dealer). This version:

  * uses the player's **real** cards,
  * draws remaining cards from the **actual remaining shoe** when a ``deck`` is
    supplied, so the estimate reflects which cards have already left the shoe —
    the same information a card counter tracks (requirement: counting must feed
    the probabilistic calculation),
  * gives the dealer a hidden hole card and plays it to 17 like the real dealer.
"""

import random

from app.core.cards import Card, SUITS, RANKS
from app.core.rules import calculate_hand_value, determine_winner


class MonteCarloSimulator:
    def __init__(self, num_simulations=500, num_decks=6):
        self.num_simulations = num_simulations
        self.num_decks = num_decks

    # -- shoe construction ------------------------------------------------
    def _remaining_shoe(self, known_cards, deck):
        """Return a list of Card objects representing the unseen shoe.

        If ``deck`` is provided we copy its remaining cards (this already
        excludes everything dealt so far). Otherwise we build a full N-deck shoe
        and remove one instance per known card.
        """
        if deck is not None and getattr(deck, "cards", None):
            return list(deck.cards)

        shoe = [Card(rank, suit)
                for suit in SUITS for rank in RANKS
                for _ in range(self.num_decks)]
        for known in known_cards:
            for i, card in enumerate(shoe):
                if card.rank == known.rank:
                    shoe.pop(i)
                    break
        return shoe

    def _simulate(self, player_hand, dealer_upcard, deck, hit_first):
        known = list(player_hand.cards) + [dealer_upcard]
        base = self._remaining_shoe(known, deck)
        if len(base) < 15:
            base = self._remaining_shoe(known, None)

        player_cards = list(player_hand.cards)
        wins = 0.0

        for _ in range(self.num_simulations):
            shoe = base[:]
            random.shuffle(shoe)

            p_cards = list(player_cards)
            # Dealer: visible up-card + one hidden hole card.
            d_cards = [dealer_upcard, shoe.pop()]

            if hit_first:
                p_cards.append(shoe.pop())

            p_val = calculate_hand_value(p_cards)
            if p_val > 21:
                continue  # player busts -> loss

            while calculate_hand_value(d_cards) < 17 and shoe:
                d_cards.append(shoe.pop())

            result = determine_winner(p_val, calculate_hand_value(d_cards))
            if result == 1:
                wins += 1
            elif result == 0:
                wins += 0.5

        return wins / self.num_simulations if self.num_simulations else 0.0

    # -- public API -------------------------------------------------------
    def simulate_hit_win_rate(self, current_player_hand, dealer_upcard, deck=None):
        """Estimated win rate if the player takes exactly one more card."""
        return self._simulate(current_player_hand, dealer_upcard, deck, hit_first=True)

    def simulate_stand_win_rate(self, current_player_hand, dealer_upcard, deck=None):
        """Estimated win rate if the player stands now."""
        return self._simulate(current_player_hand, dealer_upcard, deck, hit_first=False)
