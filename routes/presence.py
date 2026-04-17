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
        p = Presence(user_id=current_user.id)
        db.session.add(p)
    p.lat        = data.get('lat')
    p.lng        = data.get('lng')
    p.accuracy   = data.get('accuracy')
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
        return jsonify({'error': 'Ej behörig'}), 403
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=PRESENCE_TTL_MINUTES)
    # Return all presence entries (include stale ones so client can show offline)
    entries = Presence.query.join(User).order_by(User.username).all()
    result = []
    for p in entries:
        d = p.to_dict()
        d['online'] = p.updated_at is not None and p.updated_at.replace(tzinfo=timezone.utc) > cutoff
        result.append(d)
    return jsonify(result)
