from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from models import db, Presence, User

presence_bp = Blueprint('presence', __name__)

PRESENCE_TTL_MINUTES = 3

@presence_bp.post('/api/presence')
@login_required
def update_presence():
    data = request.get_json(silent=True) or {}

    p = Presence.query.filter_by(user_id=current_user.id).first()

    if p is None:
        p = Presence(
            user_id=current_user.id,
            username=current_user.username,
            role=current_user.role
        )
        db.session.add(p)
    else:
        # keep cached fields in sync
        p.username = current_user.username
        p.role = current_user.role

    p.lat = data.get('lat')
    p.lng = data.get('lng')
    p.accuracy = data.get('accuracy')
    p.working_on = data.get('working_on')
    p.updated_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({'ok': True})


@presence_bp.delete('/api/presence')
@login_required
def clear_presence():
    Presence.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'ok': True})


@presence_bp.get('/api/presence')
@login_required
def get_presence():
    if current_user.role != 'admin':
        return jsonify({'error': 'no access'}), 403

    users = Presence.query.all()

    return jsonify([
        {
            "username": u.username,
            "lat": u.lat,
            "lng": u.lng,
            "accuracy": u.accuracy,
            "working_on": u.working_on,
            "updated_at": u.updated_at.isoformat(),
            "online": (datetime.utcnow() - u.updated_at).seconds < 15
        }
        for u in users
    ])