from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Presence

users_bp = Blueprint('users', __name__)


@users_bp.get('/api/users')
@login_required
def list_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    users = User.query.order_by(User.username).all()
    return jsonify([u.to_dict() for u in users])


@users_bp.post('/api/users')
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    role     = data.get('role', 'user')

    if not username or not password:
        return jsonify({'error': 'Fyll i alla fält.'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Lösenordet måste vara minst 4 tecken.'}), 400
    if role not in ('admin', 'user'):
        return jsonify({'error': 'Ogiltig roll'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Användarnamnet är taget.'}), 409

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@users_bp.delete('/api/users/<int:uid>')
@login_required
def delete_user(uid):
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    if uid == current_user.id:
        return jsonify({'error': 'Du kan inte ta bort dig själv.'}), 400
    user = User.query.get_or_404(uid)
    # Clean up presence
    Presence.query.filter_by(user_id=uid).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'ok': True})
