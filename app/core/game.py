from .cards import Deck
from .rules import calculate_hand_value, is_bust, determine_winner
from app.ai.counter import CardCounter

class Hand:
    def __init__(self, owner_name="Player", balance=1000):
        self.owner_name = owner_name
        self.cards = []
        self.value = 0
        self.busted = False
        self.standing = False
        self.withdrawn = False
        self.balance = balance
        self.current_bet = 0
        self.initial_bet = 0 # To track for double down
        self.is_double_down = False

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
        self.dealer_hand = Hand("Dealer", balance=float('inf'))
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
            'ai_decisions_correct': 0
        }

    def start_new_round(self, num_ai=2, difficulty="HARD"):
        self.difficulty = difficulty
        if not self.players:
            self.players = [Hand("Human")]
            for i in range(num_ai):
                self.players.append(Hand(f"AI_{i+1}"))
        
        # Reset hands for new round but keep balance
        for p in self.players:
            p.cards = []
            p.value = 0
            p.busted = False
            p.standing = False
            p.withdrawn = False
            p.current_bet = 0
            p.is_double_down = False
            
            # AI Auto-bet (10% of balance, min 10)
            if "AI" in p.owner_name:
                p.place_bet(max(10, int(p.balance * 0.1)))

        self.dealer_hand.cards = []
        self.dealer_hand.value = 0
        self.dealer_hand.busted = False
        
        self.current_player_idx = 0
        self.game_over = False
        self.waiting_for_bets = True
        self.message = "Place your bets to start!"
        self.decision_history = []
        self.stats['rounds_played'] += 1

    def confirm_bets(self):
        """Called once human places bet to deal cards."""
        if not self.waiting_for_bets: return
        
        # Shuffle if needed
        if self.deck.remaining() < 20: 
            self.deck.reshuffle()
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

    def _deal_card_to(self, hand):
        card = self.deck.deal()
        self.counter.update(card)
        hand.add_card(card)

    def player_hit(self):
        if self.game_over or self.current_player_idx >= len(self.players): return
        
        player = self.players[self.current_player_idx]
        if player.standing or player.withdrawn: return
        
        self._deal_card_to(player)
        if player.busted:
            self.next_turn()

    def player_stand(self):
        if self.game_over: return
        self.players[self.current_player_idx].standing = True
        self.next_turn()

    def player_withdraw(self):
        if self.game_over: return
        self.players[self.current_player_idx].withdrawn = True
        self.next_turn()

    def next_turn(self):
        self.current_player_idx += 1
        
        # Check if next player is AI
        if self.current_player_idx < len(self.players):
            player = self.players[self.current_player_idx]
            if "AI" in player.owner_name:
                self.ai_turn(player)
        else:
            self.dealer_turn()

    def ai_turn(self, player):
        from app.ai.qlearning import QLearningAgent
        from app.ai.montecarlo import MonteCarloSimulator
        
        agent = QLearningAgent() 
        simulator = MonteCarloSimulator(num_simulations=100)
        
        while not player.busted and not player.standing:
            strategy = "Basic Rules"
            action = 0 # Default Stand
            prob_hit = 0
            
            if self.difficulty == "EASY":
                # Easy difficulty: Hit until 16, regardless of dealer
                action = 1 if player.value < 16 else 0
                strategy = "Basic Rules"
            else:
                # Hard difficulty: Use full strategy
                state_val = agent.get_state(self, player)
                action = agent.choose_action(state_val) 
                
                # Enrichment for logging
                prob_hit = simulator.simulate_hit_win_rate(player, self.dealer_hand.cards[1])
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
        
        self.next_turn()

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
        
        for i, p in enumerate(self.players):
            if p.withdrawn:
                results.append(f"{p.owner_name}: Withdrawn")
                # Withdrawn players usually lose half bet or all, let's say they keep current balance (already deducted)
                continue
            
            win_val = determine_winner(p.value, dealer_val)
            if win_val == 1:
                self.winner_indices.append(i)
                # Payout: 3:2 for Blackjack (2 cards totaling 21), 1:1 otherwise
                multiplier = 2.5 if (p.value == 21 and len(p.cards) == 2) else 2.0
                payout = int(p.current_bet * multiplier)
                p.balance += payout
                
                results.append(f"{p.owner_name}: WIN (+{payout})")
                if "Human" in p.owner_name: self.stats['player_wins'] += 1
                else: self.stats['ai_wins'] += 1
            elif win_val == -1:
                results.append(f"{p.owner_name}: LOSS")
            else:
                # Push: return bet
                p.balance += p.current_bet
                results.append(f"{p.owner_name}: DRAW")
        
        self.message = " | ".join(results)

    def get_state(self):
        return {
            'players': [p.to_dict() for p in self.players],
            'dealer_hand': self.dealer_hand.to_dict(),
            'current_player_idx': self.current_player_idx,
            'count': self.counter.running_count,
            'suggestion': self.counter.get_suggestion(),
            'game_over': self.game_over,
            'message': self.message,
            'stats': self.stats,
            'decision_history': self.decision_history
        }
