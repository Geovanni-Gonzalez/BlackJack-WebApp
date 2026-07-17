from .cards import Deck
from .rules import calculate_hand_value, is_bust, determine_winner
from app.ai.counter import CardCounter


class Hand:
    def __init__(self, owner_name="Player", balance=1000, is_ai=False, player_id=None):
        self.owner_name = owner_name
        self.player_id = player_id  # Socket ID or User ID
        self.is_ai = is_ai
        self.cards = []
        self.value = 0
        self.busted = False
        self.standing = False
        self.withdrawn = False
        self.balance = balance
        self.current_bet = 0
        self.initial_bet = 0  # To track for double down
        self.is_double_down = False
        self.is_split = False
        self.is_insurance = False
        self.split_pair_value = None

    def __setstate__(self, state):
        self.__dict__ = state
        # Backward compatibility for existing pickled sessions
        defaults = {
            'is_ai': False, 'player_id': None, 'value': 0, 'busted': False,
            'standing': False, 'withdrawn': False, 'current_bet': 0,
            'initial_bet': 0, 'is_double_down': False, 'is_split': False,
            'is_insurance': False, 'split_pair_value': None,
        }
        for key, val in defaults.items():
            if key not in self.__dict__:
                setattr(self, key, val)

    def reset_for_round(self):
        """Clear per-round state while preserving balance and identity."""
        self.cards = []
        self.value = 0
        self.busted = False
        self.standing = False
        self.withdrawn = False
        self.current_bet = 0
        self.initial_bet = 0
        self.is_double_down = False
        self.is_split = False
        self.is_insurance = False
        self.split_pair_value = None

    def add_card(self, card):
        if card is None:
            return
        self.cards.append(card)
        self.calculate()

    def place_bet(self, amount):
        if amount > self.balance:
            amount = self.balance
        self.current_bet = amount
        self.initial_bet = amount
        self.balance -= amount

    def double_bet(self):
        if self.balance >= self.initial_bet:
            self.balance -= self.initial_bet
            self.current_bet += self.initial_bet
            self.is_double_down = True
            return True
        return False

    def calculate(self):
        self.value = calculate_hand_value(self.cards)
        self.busted = is_bust(self.value)

    def to_dict(self):
        return {
            'owner': self.owner_name,
            'player_id': self.player_id,
            'is_ai': self.is_ai,
            'cards': [c.to_dict() for c in self.cards],
            'value': self.value,
            'busted': self.busted,
            'standing': self.standing,
            'withdrawn': self.withdrawn,
            'balance': self.balance,
            'bet': self.current_bet,
            'is_double': self.is_double_down,
        }


class BlackJackGame:
    def __init__(self, num_decks=6):
        self.num_decks = num_decks
        self.deck = Deck(num_decks=num_decks)
        self.counter = CardCounter()
        self.dealer_hand = Hand("Dealer", balance=1000000)
        self.players = []
        self.current_player_idx = 0
        self.game_over = True  # Starts as over until bets are placed
        self.waiting_for_bets = True
        self.difficulty = "HARD"
        self.message = "Place your bets!"
        self.decision_history = []
        self.winner_indices = []
        self.stats = {
            'rounds_played': 0,
            'player_wins': 0,
            'ai_wins': 0,
            'ai_decisions_total': 0,
            'ai_decisions_correct': 0,
            'player_decisions_total': 0,
            'player_decisions_correct': 0,
        }

    def add_player(self, name, player_id=None, balance=1000):
        """Adds a human player to the game dynamically."""
        new_hand = Hand(name, balance=balance, is_ai=False, player_id=player_id)
        self.players.append(new_hand)
        return new_hand

    def start_new_round(self, num_ai=2, difficulty="HARD"):
        """Reset all per-round state and re-open the table for betting.

        This is the critical entry point: it must clear each hand and, above
        all, set ``game_over = False`` so that hit/stand actions are honoured.
        """
        self.difficulty = difficulty

        if not self.players:
            self.players = [Hand("Human", is_ai=False)]
            for i in range(num_ai):
                self.players.append(Hand(f"AI_{i + 1}", is_ai=True))

        # Reset every hand for the new round, keeping balance and identity.
        for p in self.players:
            p.reset_for_round()
            if p.is_ai:
                p.place_bet(max(10, int(p.balance * 0.1)))

        # Fresh dealer hand.
        self.dealer_hand = Hand("Dealer", balance=1000000)

        # Reset round-level control flags.
        self.current_player_idx = 0
        self.decision_history = []
        self.winner_indices = []
        self.game_over = False          # <-- without this, hit/stand are no-ops
        self.waiting_for_bets = True
        self.message = "Place your bets!"
        self.stats['rounds_played'] += 1

    def confirm_bets(self):
        """Called once the human places a bet to deal the opening cards."""
        if not self.waiting_for_bets:
            return

        # Reshuffle the shoe if it is running low.
        if self.deck.remaining() < 20:
            self.deck = Deck(num_decks=self.num_decks)
            self.counter.reset()

        # Deal initial two cards to each player and the dealer.
        for _ in range(2):
            for p in self.players:
                self._deal_card_to(p)
            self._deal_card_to(self.dealer_hand)

        self.waiting_for_bets = False
        self.message = "Cards Dealt. Your turn!"

        # Auto-advance through any leading AI players before the human acts.
        if self.players and self.players[0].is_ai:
            self._advance_to_human_or_finish()

        if self.players and self.players[0].value == 21:
            self.message = "Blackjack! Press Stand to finish."

    def _advance_to_human_or_finish(self):
        """Play AI turns from the current index until a human must act."""
        while self.current_player_idx < len(self.players):
            player = self.players[self.current_player_idx]
            if player.is_ai:
                self.ai_turn(player)
                self.current_player_idx += 1
            else:
                return
        self.dealer_turn()

    def next_turn(self):
        self.current_player_idx += 1
        self._advance_to_human_or_finish()

    def check_game_over(self):
        """Advance the round if the current player can no longer act.

        Used by the ``/api/withdraw`` route and as a general safety net.
        """
        if self.game_over or self.waiting_for_bets:
            return
        if self.current_player_idx >= len(self.players):
            self.dealer_turn()
            return
        current = self.players[self.current_player_idx]
        if current.withdrawn or current.standing or current.busted:
            self.next_turn()

    def player_double_down(self):
        if self.game_over or self.waiting_for_bets:
            return
        p = self.players[self.current_player_idx]
        if len(p.cards) == 2 and p.balance >= p.initial_bet:
            p.double_bet()
            self._deal_card_to(p)
            p.standing = True
            self.next_turn()
        else:
            self.message = "Cannot double down (not 2 cards or insufficient funds)"

    def player_split(self):
        if self.game_over or self.waiting_for_bets:
            return
        idx = self.current_player_idx
        p = self.players[idx]

        if len(p.cards) == 2 and p.cards[0].rank == p.cards[1].rank and p.balance >= p.initial_bet:
            new_hand = Hand(p.owner_name, balance=p.balance, is_ai=p.is_ai, player_id=p.player_id)
            new_hand.is_split = True
            new_hand.current_bet = p.initial_bet
            new_hand.initial_bet = p.initial_bet

            card = p.cards.pop()
            new_hand.add_card(card)
            p.calculate()

            self._deal_card_to(p)
            self._deal_card_to(new_hand)

            self.players.insert(idx + 1, new_hand)
            self.message = "Hand Split! Playing first hand."

            self._update_owner_balance(p.owner_name, -p.initial_bet)
            self._sync_balances()
        else:
            self.message = "Cannot split (not a pair or insufficient funds)"

    def player_insurance(self):
        """Allows the human player to take insurance if the dealer shows an Ace."""
        if self.game_over or self.waiting_for_bets:
            return
        p = self.players[0]
        if (len(p.cards) == 2 and len(self.dealer_hand.cards) >= 2
                and self.dealer_hand.cards[1].rank == 'A'
                and p.balance >= p.initial_bet // 2):
            p.balance -= p.initial_bet // 2
            p.is_insurance = True
            self.message = "Insurance Taken!"
        else:
            self.message = "Cannot take insurance."

    def _sync_balances(self):
        """Ensures all hands for the same owner show the same balance."""
        owner_balances = {}
        for p in self.players:
            if p.owner_name not in owner_balances:
                owner_balances[p.owner_name] = p.balance
            else:
                p.balance = owner_balances[p.owner_name]

    def _update_owner_balance(self, owner_name, net_change):
        for p in self.players:
            if p.owner_name == owner_name:
                p.balance += net_change

    def _deal_card_to(self, hand):
        card = self.deck.deal()
        if card is None:
            self.deck = Deck(num_decks=self.num_decks)
            self.counter.reset()
            card = self.deck.deal()
        self.counter.update(card)
        hand.add_card(card)

    def player_hit(self):
        if self.game_over or self.current_player_idx >= len(self.players):
            return
        player = self.players[self.current_player_idx]
        if player.standing or player.withdrawn:
            return

        if not player.is_ai:
            self._track_human_accuracy(1)  # Action 1 = Hit

        self._deal_card_to(player)
        if player.busted:
            self.next_turn()

    def player_stand(self):
        if self.game_over:
            return
        player = self.players[self.current_player_idx]
        if not player.is_ai:
            self._track_human_accuracy(0)  # Action 0 = Stand
        player.standing = True
        self.next_turn()

    def _track_human_accuracy(self, action):
        """Compare the human move against the Monte Carlo recommendation."""
        from app.ai.factory import get_simulator
        sim = get_simulator(num_simulations=100)

        dealer_upcard = self.dealer_hand.cards[1] if len(self.dealer_hand.cards) >= 2 else None
        if dealer_upcard is None:
            return
        human = self.players[self.current_player_idx]
        p_hit = sim.simulate_hit_win_rate(human, dealer_upcard, deck=self.deck)
        p_stand = sim.simulate_stand_win_rate(human, dealer_upcard, deck=self.deck)

        self.stats['player_decisions_total'] += 1
        if (action == 1 and p_hit >= p_stand) or (action == 0 and p_stand > p_hit):
            self.stats['player_decisions_correct'] += 1

    def player_withdraw(self):
        if self.game_over:
            return
        self.players[self.current_player_idx].withdrawn = True
        self.next_turn()

    def ai_turn(self, player):
        """Play a single AI hand.

        Difficulty tiers:
          * EASY   -> fixed rule (hit until 16).
          * MEDIUM -> Monte Carlo probability only (no counting, no Q-table).
          * HARD   -> Q-Learning policy enriched with card counting.

        Note: the agent does not *learn* during live play; training happens
        offline via ``QLearningAgent.train`` / the training socket.
        """
        from app.ai.factory import get_agent, get_simulator
        agent = get_agent()
        simulator = get_simulator(num_simulations=50)

        while not player.busted and not player.standing:
            strategy = "Basic Rules"
            action = 0
            prob_hit = 0.0

            dealer_upcard = None
            if len(self.dealer_hand.cards) >= 2:
                dealer_upcard = self.dealer_hand.cards[1]
            elif len(self.dealer_hand.cards) >= 1:
                dealer_upcard = self.dealer_hand.cards[0]

            if self.difficulty == "EASY" or dealer_upcard is None:
                action = 1 if player.value < 16 else 0
                strategy = "Basic Rules"
            elif self.difficulty == "MEDIUM":
                prob_hit = simulator.simulate_hit_win_rate(player, dealer_upcard, deck=self.deck)
                prob_stand = simulator.simulate_stand_win_rate(player, dealer_upcard, deck=self.deck)
                action = 1 if prob_hit > prob_stand else 0
                strategy = "Monte Carlo"
            else:  # HARD
                state_val = agent.get_state(self, player)
                action = agent.choose_action(state_val)
                prob_hit = simulator.simulate_hit_win_rate(player, dealer_upcard, deck=self.deck)
                strategy = "Q-Learning"
                if abs(self.counter.running_count) >= 2:
                    strategy = "Card Counting"
                elif prob_hit > 0.5:
                    strategy = "Monte Carlo"

            self.decision_history.append({
                'player': player.owner_name,
                'action': "Hit" if action == 1 else "Stand",
                'reason': strategy,
                'prob_hit': prob_hit,
                'count': self.counter.running_count,
                'difficulty': self.difficulty,
            })

            self.stats['ai_decisions_total'] += 1
            if self.difficulty in ("MEDIUM", "HARD"):
                if (action == 0 and prob_hit < 0.5) or (action == 1 and prob_hit >= 0.5):
                    self.stats['ai_decisions_correct'] += 1

            if action == 1:
                self._deal_card_to(player)
                if player.busted:
                    break
            else:
                player.standing = True

    def dealer_turn(self):
        # Dealer must hit until reaching at least 17.
        while self.dealer_hand.value < 17:
            self._deal_card_to(self.dealer_hand)

        self.game_over = True
        self.determine_winners()

    def determine_winners(self):
        self.winner_indices = []
        results = []
        dealer_val = self.dealer_hand.value
        dealer_bj = (dealer_val == 21 and len(self.dealer_hand.cards) == 2)

        for i, p in enumerate(self.players):
            if p.is_insurance and dealer_bj:
                payout = (p.initial_bet // 2) * 3  # 2:1 payout + original insurance back
                self._update_owner_balance(p.owner_name, payout)
                results.append(f"{p.owner_name}: Insurance Payout (+{payout})")

            if p.withdrawn:
                results.append(f"{p.owner_name}: Withdrawn")
                continue

            win_val = determine_winner(p.value, dealer_val)
            if win_val == 1:
                self.winner_indices.append(i)
                multiplier = 2.5 if (p.value == 21 and len(p.cards) == 2 and not p.is_split) else 2.0
                payout = int(p.current_bet * multiplier)
                self._update_owner_balance(p.owner_name, payout)
                results.append(f"{p.owner_name}: WIN (+{payout})")
                if not p.is_ai:
                    self.stats['player_wins'] += 1
                else:
                    self.stats['ai_wins'] += 1
            elif win_val == -1:
                results.append(f"{p.owner_name}: LOSS")
            else:
                self._update_owner_balance(p.owner_name, p.current_bet)
                results.append(f"{p.owner_name}: DRAW")

        self.message = " | ".join(results)
        self._sync_balances()

    def get_state(self):
        return {
            'players': [p.to_dict() for p in self.players],
            'dealer_hand': self.dealer_hand.to_dict(),
            'current_player_idx': self.current_player_idx,
            'count': self.counter.running_count,
            'suggestion': self.counter.get_suggestion(),
            'game_over': self.game_over,
            'waiting_for_bets': self.waiting_for_bets,
            'message': self.message,
            'stats': self.stats,
            'decision_history': self.decision_history,
        }
