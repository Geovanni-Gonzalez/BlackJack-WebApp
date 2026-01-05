import uuid
from app.core.game import BlackJackGame
from flask_socketio import join_room, leave_room, emit

class GameManager:
    def __init__(self):
        self.rooms = {} # {room_id: BlackJackGame}
        self.player_rooms = {} # {sid: room_id}

    def create_room(self, host_sid, difficulty="HARD"):
        room_id = str(uuid.uuid4())[:6].upper()
        game = BlackJackGame()
        game.start_new_round(num_ai=0, difficulty=difficulty) # Start empty
        # Host is automatically Player 1 (Human)
        # Note: We need to map SIDs to players in the game engine to know whose turn it is
        # For simplicity, we'll append players as they join
        
        self.rooms[room_id] = game
        return room_id

    def join_room(self, room_id, sid, username):
        if room_id not in self.rooms:
            return None, "Room not found"
        
        game = self.rooms[room_id]
        
        # Check if already joined
        if sid in self.player_rooms:
            return None, "Already in a room"

        # Add player logic
        # Ideally, Game class needs to accept a specific player object or we manage mapping here
        # Let's map sid -> player index or owner name
        # For now, we assume standard flow:
        # If game has < 2 humans, allow join.
        
        # We need to modify BlackJackGame to support dynamic adding of humans?
        # Current logic: `start_new_round` resets players.
        # We might need a "Lobby Phase" where players gather before round starts.
        
        self.player_rooms[sid] = room_id
        join_room(room_id)
        return game, "Joined"

    def get_game(self, sid):
        room_id = self.player_rooms.get(sid)
        if room_id:
            return self.rooms.get(room_id)
        return None

    def remove_player(self, sid):
        if sid in self.player_rooms:
            room_id = self.player_rooms[sid]
            leave_room(room_id)
            del self.player_rooms[sid]
            # Handle game cleanup if empty?
            
game_manager = GameManager()
