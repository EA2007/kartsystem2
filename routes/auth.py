from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.post('/api/auth/login')
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': 'Fyll i alla fält.'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Fel användarnamn eller lösenord.'}), 401

    login_user(user, remember=True)
    return jsonify({'user': user.to_dict()})


@auth_bp.post('/api/auth/logout')
@login_required
def logout():
    # Clear presence on logout
    from models import Presence
    p = Presence.query.filter_by(user_id=current_user.id).first()
    if p:
        db.session.delete(p)
        db.session.commit()
    logout_user()
    return jsonify({'ok': True})


@auth_bp.get('/api/auth/me')
def me():
    if current_user.is_authenticated:
        return jsonify({'user': current_user.to_dict()})
    return jsonify({'user': None}), 401
