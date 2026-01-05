from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, PlayerModel
from .forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('web.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = PlayerModel.query.filter_by(name=form.username.data).first()
        if user and user.password_hash and check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.name
            flash('Bienvenido de nuevo!', 'success')
            return redirect(url_for('web.index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('web.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        # Check existing
        existing = PlayerModel.query.filter_by(name=form.username.data).first()
        if existing:
            flash('El nombre de usuario ya existe.', 'error')
        else:
            hashed = generate_password_hash(form.password.data)
            new_user = PlayerModel(name=form.username.data, password_hash=hashed, balance=1000)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registro exitoso! Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))
