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
    game_instance.start_new_round()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/hit', methods=['POST'])
def hit():
    game_instance.player_hit()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/stand', methods=['POST'])
def stand():
    game_instance.player_stand()
    return jsonify(game_instance.get_state())

@web_bp.route('/api/probability', methods=['GET'])
def get_probability():
    # Calculate win probability for Hit vs Stand
    if game_instance.game_over:
        return jsonify({'hit_win': 0, 'stand_win': 0})
        
    dealer_card = game_instance.dealer_hand.cards[1] # Visible card
    
    prob_hit = mc_sim.simulate_hit_win_rate(game_instance.player_hand, dealer_card)
    prob_stand = mc_sim.simulate_stand_win_rate(game_instance.player_hand, dealer_card)
    
    return jsonify({
        'hit_win_rate': prob_hit,
        'stand_win_rate': prob_stand,
        'recommendation': 'HIT' if prob_hit > prob_stand else 'STAND'
    })
