from .cards import Deck
from .rules import calculate_hand_value, is_bust, determine_winner
from app.ai.counter import CardCounter

class Hand:
    def __init__(self, owner_name="Player", balance=1000, is_ai=False):
        self.owner_name = owner_name
        self.is_ai = is_ai
        self.cards = []
        self.value = 0
        self.busted = False
        self.standing = False
        self.withdrawn = False
        self.balance = balance
        self.current_bet = 0
        self.initial_bet = 0 # To track for double down
        self.is_double_down = False
        self.is_split = False
        self.is_insurance = False
        self.split_pair_value = None 

    def __setstate__(self, state):
        self.__dict__ = state
        if 'is_ai' not in self.__dict__:
            self.is_ai = False 

    def add_card(self, card):
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
            'cards': [c.to_dict() for c in self.cards],
            'value': self.value,
            'busted': self.busted,
            'standing': self.standing,
            'withdrawn': self.withdrawn,
            'balance': self.balance,
            'bet': self.current_bet,
            'is_double': self.is_double_down
        }

class BlackJackGame:
    def __init__(self, num_decks=6):
        self.deck = Deck(num_decks=num_decks)
        self.counter = CardCounter()
        self.dealer_hand = Hand("Dealer", balance=1000000)
        self.players = [] 
        self.current_player_idx = 0
        self.game_over = True # Starts as over until bets are placed
        self.waiting_for_bets = True
        self.difficulty = "HARD"
        self.message = "Place your bets!"
        self.decision_history = [] 
        self.stats = {
            'rounds_played': 0,
            'player_wins': 0,
            'ai_wins': 0,
            'ai_decisions_total': 0,
            'ai_decisions_correct': 0,
            'player_decisions_total': 0,
            'player_decisions_correct': 0
        }

    def start_new_round(self, num_ai=2, difficulty="HARD"):
        self.difficulty = difficulty
        if not self.players:
            self.players = [Hand("Human", is_ai=False)]
            for i in range(num_ai):
                self.players.append(Hand(f"AI_{i+1}", is_ai=True))
        
        # Reset hands for new round but keep balance
        for p in self.players:
            # ... reset logic ...
            if p.is_ai:
                p.place_bet(max(10, int(p.balance * 0.1)))

    # ... (skipping unchanged parts) ...

    def next_turn(self):
        self.current_player_idx += 1
        
        while self.current_player_idx < len(self.players):
            player = self.players[self.current_player_idx]
            if player.is_ai:
                self.ai_turn(player)
                self.current_player_idx += 1
            else:
                # It's a Human player
                return
        
        self.dealer_turn()

    def confirm_bets(self):
        """Called once human places bet to deal cards."""
        if not self.waiting_for_bets: return
        
        # Shuffle if needed
        if self.deck.remaining() < 20: 
            self.deck.shuffle()
            self.counter.reset()

        # Deal initial 2 cards
        for _ in range(2):
            for p in self.players: self._deal_card_to(p)
            self._deal_card_to(self.dealer_hand)

        self.waiting_for_bets = False
        self.message = "Cards Dealt. Your turn!"
        
        # Check for natural blackjack for Human
        if self.players[0].value == 21:
            self.message = "Blackjack! Press Stand to finish."

    def player_double_down(self):
        if self.game_over or self.waiting_for_bets: return
        p = self.players[self.current_player_idx]
        if len(p.cards) == 2 and p.balance >= p.initial_bet:
            p.double_bet()
            self._deal_card_to(p)
            p.standing = True
            self.next_turn()
        else:
            self.message = "Cannot double down (not 2 cards or insufficient funds)"

    def player_split(self):
        if self.game_over or self.waiting_for_bets: return
        idx = self.current_player_idx
        p = self.players[idx]
        
        # Split conditions: 2 cards, same rank/value, enough balance
        if len(p.cards) == 2 and p.cards[0].rank == p.cards[1].rank and p.balance >= p.initial_bet:
            # Create new hand
            # The balance will be synced later, so we just need to ensure the bet is correct
            new_hand = Hand(p.owner_name, balance=p.balance) 
            new_hand.is_split = True
            
            # Place bet manually without deduction to avoid double-counting
            # since _update_owner_balance will handle the global deduction
            new_hand.current_bet = p.initial_bet
            new_hand.initial_bet = p.initial_bet
            
            # Move one card to new hand
            card = p.cards.pop()
            new_hand.add_card(card)
            p.calculate()
            
            # Deal new card to both hands
            self._deal_card_to(p)
            self._deal_card_to(new_hand)
            
            # Insert new hand after current one
            self.players.insert(idx + 1, new_hand)
            self.message = "Hand Split! Playing first hand."
            
            # Deduct once from the owner's global balance
            self._update_owner_balance(p.owner_name, -p.initial_bet)
            self._sync_balances()
        else:
            self.message = "Cannot split (not a pair or insufficient funds)"

    def player_insurance(self):
        """Allows human player to take insurance if dealer shows an Ace."""
        if self.game_over or self.waiting_for_bets: return
        p = self.players[0] # Only human for now
        # Up-card is index 1
        if len(p.cards) == 2 and len(self.dealer_hand.cards) >= 2 and self.dealer_hand.cards[1].rank == 'A' and p.balance >= p.initial_bet // 2:
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
                # If they differ, take the latest/highest? 
                # Actually, our logic should keep them in sync. 
                # Let's just force the first one's balance to others.
                p.balance = owner_balances[p.owner_name]

    def _update_owner_balance(self, owner_name, net_change):
        for p in self.players:
            if p.owner_name == owner_name:
                p.balance += net_change

    def _deal_card_to(self, hand):
        card = self.deck.deal()
        self.counter.update(card)
        hand.add_card(card)

    def player_hit(self):
        if self.game_over or self.current_player_idx >= len(self.players): return
        
        player = self.players[self.current_player_idx]
        if player.standing or player.withdrawn: return

        # Track accuracy for human player
        if player.owner_name == "Human":
            self._track_human_accuracy(1) # Action 1 = Hit

        self._deal_card_to(player)
        if player.busted:
            self.next_turn()

    def player_stand(self):
        if self.game_over: return
        player = self.players[self.current_player_idx]
        if player.owner_name == "Human":
            self._track_human_accuracy(0) # Action 0 = Stand
        player.standing = True
        self.next_turn()

    def _track_human_accuracy(self, action):
        """Helper to compare human move vs Monte Carlo."""
        # This is called via HTTP before current_state is returned, 
        # but the probability route is usually called via frontend.
        # To be accurate, we'll run a quick simulation here.
        from app.ai.montecarlo import MonteCarloSimulator
        sim = MonteCarloSimulator(num_simulations=100)
        
        dealer_upcard = self.dealer_hand.cards[1] if len(self.dealer_hand.cards) >= 2 else None
        if dealer_upcard:
            p_hit = sim.simulate_hit_win_rate(self.players[0], dealer_upcard)
            p_stand = sim.simulate_stand_win_rate(self.players[0], dealer_upcard)
            
            self.stats['player_decisions_total'] += 1
            if (action == 1 and p_hit >= p_stand) or (action == 0 and p_stand > p_hit):
                self.stats['player_decisions_correct'] += 1

    def player_withdraw(self):
        if self.game_over: return
        self.players[self.current_player_idx].withdrawn = True
        self.next_turn()

    def next_turn(self):
        self.current_player_idx += 1
        
        while self.current_player_idx < len(self.players):
            player = self.players[self.current_player_idx]
            if "AI" in player.owner_name:
                self.ai_turn(player)
                self.current_player_idx += 1
            else:
                # It's a Human player (e.g. from a split)
                return
        
        # All players finished
        self.dealer_turn()

    def ai_turn(self, player):
        from app.ai.qlearning import QLearningAgent
        from app.ai.montecarlo import MonteCarloSimulator
        
        # Instantiate locally to avoid circular import issues at class level, 
        # but consider moving to a factory if performance is an issue.
        agent = QLearningAgent() 
        simulator = MonteCarloSimulator(num_simulations=50) # Reduced for performance
        
        while not player.busted and not player.standing:
            strategy = "Basic Rules"
            action = 0 # Default Stand
            prob_hit = 0
            
            # Dealer up-card safety check
            dealer_upcard = None
            if len(self.dealer_hand.cards) >= 2:
                dealer_upcard = self.dealer_hand.cards[1]
            elif len(self.dealer_hand.cards) >= 1:
                dealer_upcard = self.dealer_hand.cards[0]

            if self.difficulty == "EASY" or dealer_upcard is None:
                # Easy difficulty: Hit until 16, regardless of dealer
                action = 1 if player.value < 16 else 0
                strategy = "Basic Rules"
            else:
                # Hard difficulty: Use full strategy
                state_val = agent.get_state(self, player)
                action = agent.choose_action(state_val) 
                
                # Enrichment for logging
                prob_hit = simulator.simulate_hit_win_rate(player, dealer_upcard)
                strategy = "Q-Learning"
                if abs(self.counter.running_count) >= 2: strategy = "Card Counting"
                elif prob_hit > 0.5: strategy = "Monte Carlo"

            self.decision_history.append({
                'player': player.owner_name,
                'action': "Hit" if action == 1 else "Stand",
                'reason': strategy,
                'prob_hit': prob_hit,
                'count': self.counter.running_count,
                'difficulty': self.difficulty
            })
            
            self.stats['ai_decisions_total'] += 1
            # Track accuracy if hard mode
            if self.difficulty == "HARD":
                if (action == 0 and prob_hit < 0.5) or (action == 1 and prob_hit >= 0.5):
                    self.stats['ai_decisions_correct'] += 1

            if action == 1:
                self._deal_card_to(player)
                if player.busted: break
            else:
                player.standing = True
        
        # Don't call next_turn here in a recursion!
        # Instead, we will handle the turn chain in the next_turn method itself.
        # But wait, ai_turn IS called by next_turn. 
        # To avoid recursion, we should use a loop or a trampoline.
        # For now, let's keep it but ensure it's the LAST thing done.
        # Actually, let's return and let next_turn handle it.

    def dealer_turn(self):
        # Dealer must hit until 17
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
            # Insurance payout
            if p.is_insurance and dealer_bj:
                payout = (p.initial_bet // 2) * 3 # 2:1 payout + original insurance bet back
                self._update_owner_balance(p.owner_name, payout)
                results.append(f"{p.owner_name}: Insurance Payout (+{payout})")

            if p.withdrawn:
                results.append(f"{p.owner_name}: Withdrawn")
                continue
            
            win_val = determine_winner(p.value, dealer_val)
            if win_val == 1:
                self.winner_indices.append(i)
                # Payout: 3:2 for Blackjack (2 cards totaling 21), 1:1 otherwise
                # Split hands usually don't get 3:2 payout in many casinos, but we'll allow it if 21
                multiplier = 2.5 if (p.value == 21 and len(p.cards) == 2 and not p.is_split) else 2.0
                payout = int(p.current_bet * multiplier)
                self._update_owner_balance(p.owner_name, payout)
                
                results.append(f"{p.owner_name}: WIN (+{payout})")
                if "Human" in p.owner_name: self.stats['player_wins'] += 1
                else: self.stats['ai_wins'] += 1
            elif win_val == -1:
                results.append(f"{p.owner_name}: LOSS")
            else:
                # Push: return bet
                self._update_owner_balance(p.owner_name, p.current_bet)
                results.append(f"{p.owner_name}: DRAW")
        
        self.message = " | ".join(results)
        self._sync_balances() # Final check

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
            'decision_history': self.decision_history
        }
