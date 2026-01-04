from flask import render_template, jsonify, request, session
from . import web_bp
from app.core.game import BlackJackGame
from app.ai.montecarlo import MonteCarloSimulator

# Global game instance for single-player demo (Not thread safe for serious prod, but fine for local demo)
game_instance = BlackJackGame()
mc_sim = MonteCarloSimulator(num_simulations=500)

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/api/start', methods=['POST'])
def start_game():
    data = request.get_json() or {}
    num_ai = data.get('num_ai', 2)
    difficulty = data.get('difficulty', 'HARD')
    game_instance.start_new_round(num_ai=num_ai, difficulty=difficulty)
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
    return jsonify(game_instance.get_state())

@web_bp.route('/api/hit', methods=['POST'])
def hit():
    game_instance.player_hit()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/stand', methods=['POST'])
def stand():
    game_instance.player_stand()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/withdraw', methods=['POST'])
def withdraw():
    game_instance.player_withdraw()
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
    
    return jsonify({
        'hit_win_rate': prob_hit,
        'stand_win_rate': prob_stand,
        'recommendation': 'HIT' if prob_hit > prob_stand else 'STAND'
    })
