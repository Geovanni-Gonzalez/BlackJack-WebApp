from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from app.core.room_manager import game_manager

socketio = SocketIO()

# --- Lobby Management ---

@socketio.on('create_room')
def on_create_room(data):
    # difficulty = data.get('difficulty', 'HARD')
    s_id = request.sid
    room_id = game_manager.create_room(s_id)
    
    # Auto-join host
    game_manager.join_room(room_id, s_id, "Host")
    game, msg = game_manager.join_room(room_id, s_id, "Host") # Returns error if already joined, handled internally?
    # Actually create_room just creates. join_room assigns.
    
    # We need to explicitly add the player to the game instance in manager
    game = game_manager.rooms[room_id]
    game.add_player("Host", player_id=s_id)
    
    join_room(room_id)
    emit('room_created', {'room_id': room_id, 'game_state': game.get_state()})

@socketio.on('join_room')
def on_join_room(data):
    room_id = data.get('room_id')
    username = data.get('username', 'Guest')
    s_id = request.sid
    
    game, msg = game_manager.join_room(room_id, s_id, username)
    if not game:
        emit('error', {'message': msg})
        return

    # Add player to game logic if not exists
    # Check if player_id already matches one
    found = False
    for p in game.players:
        if p.player_id == s_id:
            found = True
            break
    
    if not found:
        game.add_player(username, player_id=s_id)

    emit('game_joined', {'room_id': room_id, 'game_state': game.get_state()})
    emit('game_update', game.get_state(), to=room_id)


# --- Game Actions ---

def handle_game_action(action_func):
    """Helper to wrap game actions and broadcast update"""
    s_id = request.sid
    game = game_manager.get_game(s_id)
    
    if not game:
        # Fallback to session game? Or Error?
        # For MP, we require Room.
        emit('error', {'message': "Not in a multiplayer room"})
        return

    try:
        # Validate turn
        current_p = game.players[game.current_player_idx]
        if current_p.player_id != s_id:
            emit('error', {'message': "Not your turn!"})
            return

        if action_func == 'hit':
            game.player_hit()
        elif action_func == 'stand':
            game.player_stand()
        elif action_func == 'double':
            game.player_double_down()
        elif action_func == 'split':
            game.player_split()
        
        # Room ID?
        room_id = game_manager.player_rooms.get(s_id)
        if room_id:
            emit('game_update', game.get_state(), to=room_id)
            
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

@socketio.on('split')
def on_split():
    handle_game_action('split')

@socketio.on('start_round')
def on_start_round(data):
    s_id = request.sid
    game = game_manager.get_game(s_id)
    if not game: return
    
    # Only host (Player 0) should start?
    # For now, allow any player to trigger it to avoid stuck states
    
    # We need to preserve current players! 
    # game.start_new_round logic: if self.players is not empty, it keeps them.
    # But it won't add AIs if they are missing.
    
    # Check if game is actually over?
    # if not game.game_over: return # Optional safety
    
    difficulty = data.get('difficulty', 'HARD')
    game.start_new_round(num_ai=0, difficulty=difficulty) # AI count ignored if players exist
    
    room_id = game_manager.player_rooms.get(s_id)
    if room_id:
        emit('game_update', game.get_state(), to=room_id)
    
@socketio.on('connect')
def on_connect():
    pass
    # emit('message', {'data': 'Connected to Lobby System'})

@socketio.on('disconnect')
def on_disconnect():
    game_manager.remove_player(request.sid)
    # emit('message', {'data': 'Disconnected'})
    
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
