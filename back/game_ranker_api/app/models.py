from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from . import db

bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    games = db.relationship('Game', backref='owner', lazy=True)

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    criteria_data = db.Column(db.JSON, nullable=False)
    calculated_score = db.Column(db.Float)
    tier = db.Column(db.String(1))