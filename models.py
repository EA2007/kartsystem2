from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


import re

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(16), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 🛡️ security fields
    failed_logins = db.Column(db.Integer, default=0)
    locked_until  = db.Column(db.DateTime, nullable=True)

    # Relationships
    area_changes = db.relationship(
        'ActivityLog',
        backref='user_ref',
        lazy='dynamic',
        foreign_keys='ActivityLog.user_id'
    )

    # 🔐 password hashing
    def set_password(self, password):
        error = self.validate_password(password)
        if error:
            raise ValueError(error)
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 🔐 password rules
    @staticmethod
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

    # 🚫 brute-force protection
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False

    def register_failed_login(self):
        self.failed_logins += 1
        if self.failed_logins >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)

    def reset_failed_logins(self):
        self.failed_logins = 0
        self.locked_until = None

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
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
    """
    Live presence table — one row per user.
    Updated on each GPS ping (upsert pattern).
    """

    __tablename__ = 'presence'

    id = db.Column(db.Integer, primary_key=True)

    # One active presence row per user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )

    # Cached user info (faster than join for admin map)
    username = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=True)

    # GPS data
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)

    # Optional context (what user is working on)
    working_on = db.Column(db.String(120), nullable=True)

    # Last update timestamp (server controlled)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    user = db.relationship(
        'User',
        backref=db.backref('presence', uselist=False, cascade="all, delete"),
        foreign_keys=[user_id]
    )

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "lat": self.lat,
            "lng": self.lng,
            "accuracy": self.accuracy,
            "working_on": self.working_on,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
