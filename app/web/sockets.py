from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from app.web.api_routes import get_game_session, save_game_session, sync_player_db
from app.web.models import PlayerModel

# Initialize without app for blueprint-like pattern
socketio = SocketIO()

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        # Join a room based on user ID or game ID
        join_room(f"user_{session['user_id']}")
        emit('response', {'message': f'Connected as User {session["user_id"]}'})

@socketio.on('join_game')
def handle_join(data):
    # Future: Room ID for multiplayer tables
    room = "global_table" 
    join_room(room)
    emit('response', {'message': f'Joined room: {room}'})

# Actions Wrapper
def handle_game_action(action_func):
    """Helper to wrap game actions and broadcast update"""
    # print(f"[SOCKET] Received action: {action_func}")
    try:
        game = get_game_session()
        
        if action_func == 'hit':
            game.player_hit()
        elif action_func == 'stand':
            game.player_stand()
        elif action_func == 'double':
            game.player_double_down()
        elif action_func == 'split':
            game.player_split()
        
        sync_player_db(game)
        save_game_session(game)
        
        emit('game_update', game.get_state())
    except Exception as e:
        print(f"[SOCKET ERROR] {e}")
        import traceback
        traceback.print_exc()

@socketio.on('hit')
def on_hit():
    handle_game_action('hit')

@socketio.on('stand')
def on_stand():
    handle_game_action('stand')

@socketio.on('double')
def on_double():
    handle_game_action('double')
    
@socketio.on('start_training')
def handle_training(data):
    """Simulate training episodes and stream results"""
    episodes = data.get('episodes', 100)
    wins = 0
    # Dummy simulation for visual effect (Real training would take time)
    # in a real scenario we would call QLearningAgent.train()
    
    import time
    from app.ai.qlearning import QLearningAgent
    agent = QLearningAgent()
    
    for i in range(1, episodes + 1):
        # Simulate quick game or use agent
        # For simplicity in this demo, we emit fake progress
        # Real implementation would be inside agent loop
        
        if i % 10 == 0:
            emit('training_update', {
                'episode': i,
                'win_rate': 0.42 + (i / episodes * 0.05), # Fake improvement
                'epsilon': 1.0 - (i / episodes),
            })
            time.sleep(0.01) # Small delay to see animation
