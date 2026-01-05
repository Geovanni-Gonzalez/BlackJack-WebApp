from flask import render_template, jsonify, request, session
from . import web_bp
from app.core.game import BlackJackGame
from app.ai.montecarlo import MonteCarloSimulator
from .models import db, PlayerModel, GameSession

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
    game_instance.player_hit()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/stand', methods=['POST'])
def stand():
    game_instance.player_stand()
    sync_player_db()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/withdraw', methods=['POST'])
def withdraw():
    game_instance.player_withdraw()
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
