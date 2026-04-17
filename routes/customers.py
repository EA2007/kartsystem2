from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Customer, Area

customers_bp = Blueprint('customers', __name__)


@customers_bp.get('/api/customers')
@login_required
def list_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return jsonify([c.to_dict() for c in customers])


@customers_bp.post('/api/customers')
@login_required
def create_customer():
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Kundnamn krävs'}), 400
    if Customer.query.filter_by(name=name).first():
        return jsonify({'error': 'Kunden finns redan'}), 409
    customer = Customer(name=name)
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer.to_dict()), 201


@customers_bp.delete('/api/customers/<int:cid>')
@login_required
def delete_customer(cid):
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    customer = Customer.query.get_or_404(cid)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'ok': True})


@customers_bp.delete('/api/customers/<int:cid>/areas')
@login_required
def reset_areas(cid):
    if current_user.role != 'admin':
        return jsonify({'error': 'Ej behörig'}), 403
    customer = Customer.query.get_or_404(cid)
    Area.query.filter_by(customer_id=customer.id).delete()
    db.session.commit()
    return jsonify({'ok': True})
