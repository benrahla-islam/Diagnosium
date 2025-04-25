from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .routes import routes

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change-this-to-a-random-key-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)
    
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprint
    app.register_blueprint(routes)
    
    with app.app_context():
        db.create_all()
    
    return app