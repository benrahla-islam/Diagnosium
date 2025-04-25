from flask import Flask
from models import db, User
from routes import login_manager, routes as views

# Ensure db is initialized before being imported by models or views

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diagnosium.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    login_manager.login_view = 'auth.login'  # Changed from 'routes.login' to 'auth.login'
    login_manager.init_app(app)
    

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(views, url_prefix='/')

    create_database(app)

    return app

def create_database(app):
    with app.app_context():
        db.create_all()
        