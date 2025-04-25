from flask_login import UserMixin
# from diagnosium_front import db
# from sqlalchemy.dialects.postgresql import JSON
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import json



db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(200))
    subscription = db.Column(Enum('Free', 'Pro'), default='Free')
    conversations = db.relationship('Conversation', backref='user', lazy=True)

    def __init__(self, email, name, password):
        self.email = email
        self.name = name
        self.password = password
        self.subscription = 'Free'


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Using JSON type for PostgreSQL or
    # content = db.Column()
    # For other databases that don't support JSON natively:
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, user_id, content):
        self.user_id = user_id
        self.content = content

    def set_content_json(self, content_dict):
        """Store a dictionary as JSON in the database"""
        if isinstance(self.content, str):
            # If using Text type instead of JSON
            self.content = json.dumps(content_dict)
        else:
            # If using native JSON type
            self.content = content_dict
    
    def get_content_json(self):
        """Get the content as a Python dictionary"""
        if isinstance(self.content, str):
            # If using Text type instead of JSON
            return json.loads(self.content)
        else:
            # If using native JSON type
            return self.content