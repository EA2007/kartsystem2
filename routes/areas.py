from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db, Customer, Area, ActivityLog
import json, uuid

areas_bp = Blueprint('areas', __name__)


@areas_bp.get('/api/customers/<int:cid>/areas')
@login_required
def get_areas(cid):
    customer = Customer.query.get_or_404(cid)
    return jsonify([a.to_dict() for a in customer.areas.all()])


@areas_bp.put('/api/customers/<int:cid>/areas')
@login_required
def save_areas(cid):
    """Full replace — client sends the complete list of areas for this customer."""
    customer = Customer.query.get_or_404(cid)
    data = request.get_json(silent=True) or []

    incoming_uids = {item['uid'] for item in data if item.get('uid')}

    # Delete areas that were removed on client
    for area in customer.areas.all():
        if area.uid not in incoming_uids:
            db.session.delete(area)

    for item in data:
        uid = item.get('uid') or str(uuid.uuid4()).replace('-', '')[:16]
        area = Area.query.filter_by(uid=uid).first()
        if area is None:
            area = Area(uid=uid, customer_id=customer.id)
            db.session.add(area)

        old_status = area.status
        area.geojson = json.dumps(item.get('geojson', {}))
        area.status  = item.get('status', 'new')

        # Track status changes
        if old_status != area.status or area.id is None:
            area.last_user_id = current_user.id
            area.last_changed = datetime.now(timezone.utc)
            log = ActivityLog(
                user_id     = current_user.id,
                customer_id = customer.id,
                area_uid    = uid,
                from_status = old_status,
                to_status   = area.status,
            )
            db.session.add(log)

    db.session.commit()
    return jsonify([a.to_dict() for a in customer.areas.all()])


@areas_bp.patch('/api/areas/<string:uid>/status')
@login_required
def update_status(uid):
    """Quick single-area status update."""
    area = Area.query.filter_by(uid=uid).first_or_404()
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ('new', 'started', 'done'):
        return jsonify({'error': 'Ogiltig status'}), 400

    old_status = area.status
    area.status = new_status
    area.last_user_id = current_user.id
    area.last_changed = datetime.now(timezone.utc)

    log = ActivityLog(
        user_id     = current_user.id,
        customer_id = area.customer_id,
        area_uid    = uid,
        from_status = old_status,
        to_status   = new_status,
    )
    db.session.add(log)
    db.session.commit()
    return jsonify(area.to_dict())
