from flask import Blueprint, jsonify, request, session, current_app
from app.core.game import BlackJackGame
from app.ai.montecarlo import MonteCarloSimulator
from .models import db, PlayerModel, Leaderboard
from app.ai.qlearning import QLearningAgent

api_bp = Blueprint('api', __name__)

# MC Simulator is stateless enough to be global for now (caches will handle optimization)
mc_sim = MonteCarloSimulator(num_simulations=500)

def get_game_session():
    """Retrieve or create a game session for the current user."""
    if 'game' not in session:
        session['game'] = BlackJackGame()
    return session['game']

def save_game_session(game):
    """Save the game state back to the session."""
    session['game'] = game

def sync_player_db(game):
    """Sync key player stats to DB."""
    try:
        if game.game_over and len(game.players) > 0:
            if 'user_id' in session:
                player = PlayerModel.query.get(session['user_id'])
                if player:
                    player.balance = game.players[0].balance
                    db.session.commit()
    except Exception as e:
        print(f"Database Sync Error: {e}")
        db.session.rollback()

@api_bp.route('/start', methods=['POST'])
def start_game():
    game = get_game_session()
    data = request.get_json() or {}
    num_ai = int(data.get('num_ai', 2))
    difficulty = data.get('difficulty', 'HARD')
    
    # Validation
    if not (0 <= num_ai <= 5): num_ai = 2
    if difficulty not in ['EASY', 'MEDIUM', 'HARD']: difficulty = 'HARD'
    
    # DB Persistence LINKED TO AUTH
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = PlayerModel.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'error': 'User not found, re-login required'}), 401
        
    game.start_new_round(num_ai=num_ai, difficulty=difficulty)
    # Set player name to auth username
    game.players[0].owner_name = user.name
    # Sync balance from DB
    game.players[0].balance = user.balance
    
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/bet', methods=['POST'])
def place_bet():
    game = get_game_session()
    data = request.get_json()
    amount = int(data.get('amount', 10))
    if amount < 1: amount = 10
    
    if game.players:
        game.players[0].place_bet(amount)
        game.confirm_bets()
    
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/hit', methods=['POST'])
def hit():
    game = get_game_session()
    game.player_hit()
    sync_player_db(game)
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/stand', methods=['POST'])
def stand():
    game = get_game_session()
    game.player_stand()
    sync_player_db(game)
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/double', methods=['POST'])
def double_down():
    game = get_game_session()
    game.player_double_down()
    sync_player_db(game)
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/split', methods=['POST'])
def split():
    game = get_game_session()
    game.player_split()
    sync_player_db(game)
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/insurance', methods=['POST'])
def insurance():
    game = get_game_session()
    game.player_insurance()
    sync_player_db(game)
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/withdraw', methods=['POST'])
def withdraw_game():
    game = get_game_session()
    if game.players:
        game.players[0].withdrawn = True
        game.check_game_over()
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/refill', methods=['POST'])
def refill_balance():
    game = get_game_session()
    if game.players:
        game.players[0].balance = 1000
    sync_player_db(game)
    save_game_session(game)
    return jsonify(game.get_state())

@api_bp.route('/probability', methods=['GET'])
def get_probability():
    game = get_game_session()
    if game.game_over or game.waiting_for_bets:
        return jsonify({'hit_win': 0, 'stand_win': 0})
        
    dealer_card = game.dealer_hand.cards[1]
    current_hand = game.players[game.current_player_idx]
    
    # Use cached wrapper or direct call (will add cache later)
    prob_hit = mc_sim.simulate_hit_win_rate(current_hand, dealer_card)
    prob_stand = mc_sim.simulate_stand_win_rate(current_hand, dealer_card)
    
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

@api_bp.route('/qvalues', methods=['GET'])
def get_qvalues():
    game = get_game_session()
    if game.game_over or game.waiting_for_bets:
        return jsonify({'q_stand': 0, 'q_hit': 0, 'state': None})
    
    agent = QLearningAgent()
    current_hand = game.players[game.current_player_idx]
    state = agent.get_state(game, current_hand)
    q_vals = agent.get_q_values(state)
    
    return jsonify({
        'q_stand': round(q_vals[0], 3),
        'q_hit': round(q_vals[1], 3),
        'state': str(state),
        'optimal_action': 'Stand' if q_vals[0] >= q_vals[1] else 'Hit'
    })

@api_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    entries = Leaderboard.query.order_by(Leaderboard.peak_balance.desc()).limit(10).all()
    return jsonify([entry.to_dict() for entry in entries])

@api_bp.route('/leaderboard', methods=['POST'])
def save_leaderboard():
    game = get_game_session()
    try:
        if not game.players or len(game.players) == 0:
            return jsonify({'success': False, 'message': 'No player data'})
        
        player = game.players[0]
        stats = game.stats
        
        total_games = stats['player_wins'] + stats.get('ai_wins', 0)
        win_rate = (stats['player_wins'] / total_games * 100) if total_games > 0 else 0
        
        ai_acc = (stats['ai_decisions_correct'] / stats['ai_decisions_total'] * 100) if stats['ai_decisions_total'] > 0 else 0
        player_acc = (stats['player_decisions_correct'] / stats['player_decisions_total'] * 100) if stats['player_decisions_total'] > 0 else 0
        
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
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@api_bp.route('/strategy/heatmap', methods=['GET'])
def get_strategy_heatmap():
    try:
        agent = QLearningAgent()
        heatmap = agent.generate_strategy_heatmap()
        return jsonify({
            'heatmap': heatmap,
            'rows': list(range(4, 22)),
            'cols': list(range(2, 12)),
            'legend': {0: 'Stand', 1: 'Hit', 2: 'Equal'}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/strategy/details', methods=['GET'])
def get_strategy_details():
    try:
        player_sum = int(request.args.get('player_sum', 15))
        dealer_card = int(request.args.get('dealer_card', 10))
        agent = QLearningAgent()
        details = agent.get_strategy_details(player_sum, dealer_card)
        return jsonify({'player_sum': player_sum, 'dealer_card': dealer_card, 'details': details})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/strategy/compare', methods=['GET'])
def compare_strategies():
    try:
        agent = QLearningAgent()
        comparison = agent.compare_with_basic_strategy()
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
