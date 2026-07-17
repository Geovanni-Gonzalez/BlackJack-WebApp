from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from app.core.room_manager import game_manager

socketio = SocketIO()

# --- Lobby Management ---

@socketio.on('create_room')
def on_create_room(data):
    s_id = request.sid
    room_id = game_manager.create_room(s_id)
    game_manager.join_room(room_id, s_id, "Host")
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
    found = any(p.player_id == s_id for p in game.players)
    if not found:
        game.add_player(username, player_id=s_id)
    emit('game_joined', {'room_id': room_id, 'game_state': game.get_state()})
    emit('game_update', game.get_state(), to=room_id)


# --- Game Actions ---

def handle_game_action(action_func):
    """Helper to wrap game actions and broadcast update."""
    s_id = request.sid
    game = game_manager.get_game(s_id)
    if not game:
        emit('error', {'message': "Not in a multiplayer room"})
        return
    try:
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
    if not game:
        return
    if game.players and game.players[0].player_id != s_id:
        emit('error', {'message': "Solo el anfitrion puede iniciar una nueva ronda."})
        return
    difficulty = data.get('difficulty', 'HARD')
    game.start_new_round(num_ai=0, difficulty=difficulty)
    room_id = game_manager.player_rooms.get(s_id)
    if room_id:
        emit('game_update', game.get_state(), to=room_id)

@socketio.on('connect')
def on_connect():
    pass

@socketio.on('disconnect')
def on_disconnect():
    game_manager.remove_player(request.sid)

@socketio.on('start_training')
def handle_training(data):
    """Run real Q-Learning training in chunks and stream actual progress."""
    from app.ai.factory import get_agent
    episodes = int(data.get('episodes', 100))
    episodes = max(10, min(episodes, 5000))
    agent = get_agent()
    chunk = max(1, episodes // 20)
    cumulative_wins = 0
    cumulative_total = 0
    done = 0
    while done < episodes:
        batch = min(chunk, episodes - done)
        wins, losses, draws = agent.train(num_episodes=batch)
        cumulative_wins += wins
        cumulative_total += (wins + losses + draws)
        done += batch
        win_rate = (cumulative_wins / cumulative_total) if cumulative_total else 0.0
        emit('training_update', {
            'episode': done,
            'win_rate': round(win_rate, 4),
            'epsilon': agent.epsilon,
            'q_states': len(agent.q_table),
        })
        socketio.sleep(0)
    final_rate = (cumulative_wins / cumulative_total) if cumulative_total else 0.0
    emit('training_complete', {
        'episodes': done,
        'win_rate': round(final_rate, 4),
        'q_states': len(agent.q_table),
    })
