from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://aiy:236632@localhost:5432/tier_db')
    app.config['JWT_SECRET_KEY'] = 'your-secret-key'

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app