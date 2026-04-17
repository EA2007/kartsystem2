from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import ActivityLog

activity_bp = Blueprint('activity', __name__)


@activity_bp.get('/api/activity')
@login_required
def get_activity():
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    customer_id = request.args.get('customer_id', type=int)
    limit       = min(request.args.get('limit', 100, type=int), 500)
    q = ActivityLog.query.order_by(ActivityLog.timestamp.desc())
    if customer_id:
        q = q.filter_by(customer_id=customer_id)
    logs = q.limit(limit).all()
    return jsonify([l.to_dict() for l in logs])
