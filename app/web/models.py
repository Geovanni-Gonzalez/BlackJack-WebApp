from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PlayerModel(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    rounds_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False)
    peak_balance = db.Column(db.Integer, nullable=False)
    rounds_played = db.Column(db.Integer, nullable=False)
    win_rate = db.Column(db.Float, nullable=False)  # Percentage
    ai_accuracy = db.Column(db.Float, default=0.0)
    player_accuracy = db.Column(db.Float, default=0.0)
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_name': self.player_name,
            'peak_balance': self.peak_balance,
            'rounds_played': self.rounds_played,
            'win_rate': round(self.win_rate, 1),
            'ai_accuracy': round(self.ai_accuracy, 1),
            'player_accuracy': round(self.player_accuracy, 1),
            'achieved_at': self.achieved_at.strftime('%Y-%m-%d %H:%M')
        }
