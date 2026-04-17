from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(16), nullable=False, default='user')  # 'admin' | 'user'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    area_changes = db.relationship('ActivityLog', backref='user_ref', lazy='dynamic',
                                   foreign_keys='ActivityLog.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Customer(db.Model):
    __tablename__ = 'customers'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    areas = db.relationship('Area', backref='customer', lazy='dynamic',
                            cascade='all, delete-orphan')

    def to_dict(self):
        areas = self.areas.all()
        done    = sum(1 for a in areas if a.status == 'done')
        started = sum(1 for a in areas if a.status == 'started')
        return {
            'id': self.id,
            'name': self.name,
            'area_count': len(areas),
            'done_count': done,
            'started_count': started,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Area(db.Model):
    __tablename__ = 'areas'

    id          = db.Column(db.Integer, primary_key=True)
    uid         = db.Column(db.String(32), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    geojson     = db.Column(db.Text, nullable=False)          # GeoJSON string
    status      = db.Column(db.String(16), nullable=False, default='new')  # new|started|done
    last_user_id= db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_changed= db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    last_user   = db.relationship('User', foreign_keys=[last_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'geojson': json.loads(self.geojson) if self.geojson else None,
            'status': self.status,
            'last_user': self.last_user.username if self.last_user else None,
            'last_changed': self.last_changed.isoformat() if self.last_changed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    area_uid    = db.Column(db.String(32), nullable=True)
    from_status = db.Column(db.String(16), nullable=True)
    to_status   = db.Column(db.String(16), nullable=True)
    timestamp   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    customer    = db.relationship('Customer', foreign_keys=[customer_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user_ref.username if self.user_ref else 'unknown',
            'customer': self.customer.name if self.customer else None,
            'area_uid': self.area_uid,
            'from_status': self.from_status,
            'to_status': self.to_status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class Presence(db.Model):
    """Live presence — one row per online user, upserted on each GPS ping."""
    __tablename__ = 'presence'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    lat         = db.Column(db.Float, nullable=True)
    lng         = db.Column(db.Float, nullable=True)
    accuracy    = db.Column(db.Float, nullable=True)
    working_on  = db.Column(db.String(120), nullable=True)
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    user        = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'username': self.user.username if self.user else None,
            'role': self.user.role if self.user else None,
            'lat': self.lat,
            'lng': self.lng,
            'accuracy': self.accuracy,
            'working_on': self.working_on,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
