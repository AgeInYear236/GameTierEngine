from flask import Blueprint, request, jsonify
from .models import db, User, Game
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import traceback
from sqlalchemy import func
import urllib


main_bp = Blueprint('main_bp', __name__)
bcrypt = Bcrypt()

@main_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # Check if user exists first to prevent errors
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400
    
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password_hash=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

@main_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        # FIX: Ensure user.id is converted to a string here
        token = create_access_token(identity=str(user.id)) 
        return jsonify({"token": token}), 200
        
    return jsonify({"msg": "Invalid credentials"}), 401

@main_bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Game Ranker API is running!"})

@main_bp.route('/get_games', methods=['GET'])
@jwt_required()
def get_games():
    user_id = get_jwt_identity()
    games = Game.query.filter_by(user_id=int(user_id)).all()
    
    # Map the database objects to a JSON-friendly list of dictionaries
    game_list = [{
        "game_name": g.game_name,
        "criteria_scores": g.criteria_data,
        "calculated_score": g.calculated_score,
        "tier": g.tier
    } for g in games]
    
    return jsonify(game_list), 200

@main_bp.route('/save_game', methods=['POST'])
@jwt_required()
def save_game():
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}") # Log what we got
        
        user_id = get_jwt_identity()
        
        new_game = Game(
            user_id=int(user_id),
            game_name=data.get('game_name'),
            criteria_data=data.get('criteria_scores'),
            calculated_score=data.get('calculated_score'),
            tier=data.get('tier')
        )
        
        db.session.add(new_game)
        db.session.commit()
        return jsonify({"msg": "Success"}), 201
    except Exception:
        print(traceback.format_exc()) # THIS WILL PRINT THE ACTUAL ERROR
        return jsonify({"msg": "Server Error"}), 500

@main_bp.route('/delete_game/<game_name>', methods=['DELETE'])
@jwt_required()
def delete_game(game_name):
    user_id = get_jwt_identity()
    # Decode the name in case of spaces/special characters
    decoded_name = urllib.parse.unquote(game_name)
    
    # Query to ensure the user only deletes their own games
    game = Game.query.filter_by(user_id=int(user_id), game_name=decoded_name).first()
    
    if game:
        db.session.delete(game)
        db.session.commit()
        return jsonify({"msg": "Game deleted successfully"}), 200
    
    return jsonify({"msg": "Game not found or access denied"}), 404

@main_bp.route('/users_stats', methods=['GET'])
def get_users_stats():
    # Query all users and count their associated games
    stats = db.session.query(
        User.username, 
        func.count(Game.id).label('game_count')
    ).outerjoin(Game).group_by(User.username).all()
    
    return jsonify([{"username": s.username, "game_count": s.game_count} for s in stats]), 200

@main_bp.route('/search_games', methods=['GET'])
def search_games():
    query = request.args.get('q', '')
    # Query: Get game name and average of their calculated scores
    stats = db.session.query(
        Game.game_name,
        func.avg(Game.calculated_score).label('avg_score'),
        func.count(Game.id).label('review_count')
    ).filter(Game.game_name.ilike(f'%{query}%')) \
     .group_by(Game.game_name).all()
    
    return jsonify([{
        "name": s.game_name, 
        "avg_score": round(s.avg_score, 2), 
        "count": s.review_count
    } for s in stats]), 200

@main_bp.route('/get_user_games/<username>', methods=['GET'])
def get_user_games(username):
    # Find user by username
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    games = Game.query.filter_by(user_id=user.id).all()
    output = [{
        "game_name": g.game_name,
        "criteria_scores": g.criteria_data,
        "calculated_score": g.calculated_score,
        "tier": g.tier
    } for g in games]
    return jsonify(output), 200