from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from diagnosium_front.models import User
from diagnosium_front.models import db

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    return render_template('home.html')


@routes.route('/pricing')
def pricing():
    return render_template('pricing.html')

@routes.route('/about')
def about():
    return render_template('about.html')

@routes.route('/chat')
def chat():
    return render_template('chat.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('routes.index'))
        else:
            flash('Please check your login details and try again.', 'danger')
    
    return render_template('login.html')

@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('signup.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists!', 'danger')
            return render_template('signup.html')
        
        new_user = User(
            email=email, 
            name=name, 
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('routes.login'))
    
    return render_template('signup.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))