from flask import Blueprint, render_template, request, redirect, url_for

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