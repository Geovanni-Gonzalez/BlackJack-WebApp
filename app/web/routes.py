from flask import render_template, redirect, url_for, session
from . import web_bp
from .models import PlayerModel

@web_bp.route('/favicon.ico')
def favicon():
    return '', 204

@web_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # Optional: Pass user info to template if needed
    user = PlayerModel.query.get(session['user_id'])
    return render_template('index.html', user=user)

@web_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')
