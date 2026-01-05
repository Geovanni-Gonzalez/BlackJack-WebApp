from flask import render_template, jsonify, request, session
from . import web_bp
from app.core.game import BlackJackGame
from app.ai.montecarlo import MonteCarloSimulator
from .models import db, PlayerModel, GameSession, Leaderboard

# Global game instance
game_instance = BlackJackGame()
mc_sim = MonteCarloSimulator(num_simulations=500)

def sync_player_db():
    try:
        if game_instance.game_over and len(game_instance.players) > 0:
            player_name = "Human" 
            player = PlayerModel.query.filter_by(name=player_name).first()
            if player:
                # Always sync from the first hand (the owner's primary balance)
                player.balance = game_instance.players[0].balance
                db.session.commit()
    except Exception as e:
        print(f"Database Sync Error: {e}")
        db.session.rollback()

@web_bp.route('/favicon.ico')
def favicon():
    return '', 204

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/api/start', methods=['POST'])
def start_game():
    print("\n[BACKEND] -> POST /api/start")
    data = request.get_json() or {}
    num_ai = data.get('num_ai', 2)
    difficulty = data.get('difficulty', 'HARD')
    
    # Database Persistence
    player_name = "Human" # Simplified for single-user local demo
    player = PlayerModel.query.filter_by(name=player_name).first()
    if not player:
        player = PlayerModel(name=player_name, balance=1000)
        db.session.add(player)
        db.session.commit()
    
    game_instance.start_new_round(num_ai=num_ai, difficulty=difficulty)
    # Sync balance from DB to Game Engine
    game_instance.players[0].balance = player.balance
    
    return jsonify(game_instance.get_state())

@web_bp.route('/api/bet', methods=['POST'])
def place_bet():
    print("\n[BACKEND] -> POST /api/bet")
    data = request.get_json()
    amount = data.get('amount', 10)
    # Human is always index 0
    game_instance.players[0].place_bet(amount)
    game_instance.confirm_bets()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/double', methods=['POST'])
def double_down():
    game_instance.player_double_down()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/split', methods=['POST'])
def split():
    game_instance.player_split()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/insurance', methods=['POST'])
def insurance():
    game_instance.player_insurance()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/hit', methods=['POST'])
def hit():
    print("\n[BACKEND] -> POST /api/hit")
    game_instance.player_hit()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/stand', methods=['POST'])
def stand():
    print("\n[BACKEND] -> POST /api/stand")
    game_instance.player_stand()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/withdraw', methods=['POST'])
def withdraw_game():
    game_instance.players[0].withdrawn = True
    game_instance.check_game_over()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/refill', methods=['POST'])
def refill_balance():
    print("\n[BACKEND] -> POST /api/refill")
    # Reset human balance
    game_instance.players[0].balance = 1000
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/probability', methods=['GET'])
def get_probability():
    # Calculate win probability for Hit vs Stand
    if game_instance.game_over or game_instance.waiting_for_bets:
        return jsonify({'hit_win': 0, 'stand_win': 0})
        
    dealer_card = game_instance.dealer_hand.cards[1] # Visible card
    current_hand = game_instance.players[game_instance.current_player_idx]
    
    prob_hit = mc_sim.simulate_hit_win_rate(current_hand, dealer_card)
    prob_stand = mc_sim.simulate_stand_win_rate(current_hand, dealer_card)
    
    # Simple Strategy Explanation (Spanish)
    reason = "Análisis probabilístico"
    p_val = current_hand.value
    d_val = dealer_card.value
    
    if p_val <= 11:
        reason = "Tu mano es baja, siempre es seguro pedir."
    elif p_val >= 17:
        reason = "Mano fuerte, el riesgo de pasarse es muy alto."
    elif 2 <= d_val <= 6:
        reason = f"El Dealer tiene carta débil ({d_val}), podría pasarse."
    elif d_val >= 7:
        reason = f"El Dealer tiene carta fuerte ({d_val}), necesitas sumar más."

    return jsonify({
        'hit_win_rate': prob_hit,
        'stand_win_rate': prob_stand,
        'recommendation': 'PEDIR (Hit)' if prob_hit > prob_stand else 'PLANTARSE (Stand)',
        'reason': reason
    })

@web_bp.route('/api/qvalues', methods=['GET'])
def get_qvalues():
    """Returns Q-Learning values for the current state to visualize AI confidence."""
    if game_instance.game_over or game_instance.waiting_for_bets:
        return jsonify({'q_stand': 0, 'q_hit': 0, 'state': None})
    
    from app.ai.qlearning import QLearningAgent
    agent = QLearningAgent()
    
    current_hand = game_instance.players[game_instance.current_player_idx]
    state = agent.get_state(game_instance, current_hand)
    q_vals = agent.get_q_values(state)
    
    return jsonify({
        'q_stand': round(q_vals[0], 3),
        'q_hit': round(q_vals[1], 3),
        'state': str(state),
        'optimal_action': 'Stand' if q_vals[0] >= q_vals[1] else 'Hit'
    })

@web_bp.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Returns top 10 leaderboard entries."""
    entries = Leaderboard.query.order_by(Leaderboard.peak_balance.desc()).limit(10).all()
    return jsonify([entry.to_dict() for entry in entries])

@web_bp.route('/api/leaderboard', methods=['POST'])
def save_leaderboard():
    """Saves current session to leaderboard if it qualifies."""
    try:
        if not game_instance.players or len(game_instance.players) == 0:
            return jsonify({'success': False, 'message': 'No player data'})
        
        player = game_instance.players[0]
        stats = game_instance.stats
        
        # Calculate win rate
        total_games = stats['player_wins'] + stats.get('ai_wins', 0)
        win_rate = (stats['player_wins'] / total_games * 100) if total_games > 0 else 0
        
        # Calculate accuracies
        ai_acc = (stats['ai_decisions_correct'] / stats['ai_decisions_total'] * 100) if stats['ai_decisions_total'] > 0 else 0
        player_acc = (stats['player_decisions_correct'] / stats['player_decisions_total'] * 100) if stats['player_decisions_total'] > 0 else 0
        
        # Create leaderboard entry
        entry = Leaderboard(
            player_name=player.owner_name,
            peak_balance=player.balance,
            rounds_played=stats['rounds_played'],
            win_rate=win_rate,
            ai_accuracy=ai_acc,
            player_accuracy=player_acc
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Entrada guardada en el Hall of Fame!'})
    except Exception as e:
        print(f"Leaderboard Save Error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@web_bp.route('/api/strategy/heatmap', methods=['GET'])
def get_strategy_heatmap():
    """Returns the Q-Learning strategy heatmap for visualization."""
    try:
        from app.ai.qlearning import QLearningAgent
        agent = QLearningAgent()
        
        heatmap = agent.generate_strategy_heatmap()
        
        return jsonify({
            'heatmap': heatmap,
            'rows': list(range(4, 22)),  # Player sums
            'cols': list(range(2, 12)),  # Dealer cards
            'legend': {
                0: 'Stand',
                1: 'Hit',
                2: 'Equal'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/strategy/details', methods=['GET'])
def get_strategy_details():
    """Returns detailed Q-values for a specific state."""
    try:
        player_sum = int(request.args.get('player_sum', 15))
        dealer_card = int(request.args.get('dealer_card', 10))
        
        from app.ai.qlearning import QLearningAgent
        agent = QLearningAgent()
        
        details = agent.get_strategy_details(player_sum, dealer_card)
        
        return jsonify({
            'player_sum': player_sum,
            'dealer_card': dealer_card,
            'details': details
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/strategy/compare', methods=['GET'])
def compare_strategies():
    """Compares Q-Learning strategy with basic Blackjack strategy."""
    try:
        from app.ai.qlearning import QLearningAgent
        agent = QLearningAgent()
        
        comparison = agent.compare_with_basic_strategy()
        
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
