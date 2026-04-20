from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re, time

auth_bp = Blueprint('auth', __name__)

# 🛡️ simple rate limit (per IP)
login_attempts = {}

def is_blocked(ip):
    attempts = login_attempts.get(ip, [])
    now = time.time()

    # keep only last 60 seconds
    attempts = [t for t in attempts if now - t < 60]

    if len(attempts) >= 5:
        return True

    attempts.append(now)
    login_attempts[ip] = attempts
    return False


# 🔐 password validation (use for register later)
def validate_password(password):
    if len(password) < 8:
        return "Minst 8 tecken"
    if not re.search(r"[A-Z]", password):
        return "Minst en stor bokstav"
    if not re.search(r"[a-z]", password):
        return "Minst en liten bokstav"
    if not re.search(r"[0-9]", password):
        return "Minst en siffra"
    return None


@auth_bp.post('/api/auth/login')
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    ip = request.remote_addr

    # 🚫 block too many attempts
    if is_blocked(ip):
        return jsonify({'error': 'För många försök. Vänta 1 minut.'}), 429

    if not username or not password:
        return jsonify({'error': 'Fyll i alla fält.'}), 400

    user = User.query.filter_by(username=username).first()

    # ❌ wrong login
    if not user or not user.check_password(password):
        return jsonify({'error': 'Fel användarnamn eller lösenord.'}), 401

    # ✔ successful login → reset attempts
    login_attempts[ip] = []

    login_user(user, remember=True)
    return jsonify({'user': user.to_dict()})


@auth_bp.post('/api/auth/logout')
@login_required
def logout():
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