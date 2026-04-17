import os
from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User
from routes import all_blueprints
from config import config


def create_app(env=None):
    app = Flask(__name__)

    # Load config
    env = env or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[env])

    # Init extensions
    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = None  # API returns 401, frontend handles redirect

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return {'error': 'Ej inloggad'}, 401

    # Register all blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Serve the SPA
    @app.get('/')
    def index():
        return render_template('index.html')

    # Create tables and seed admin on first run
    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create default admin if none exists."""
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print('✓ Admin user created (admin / admin123) — change the password!')


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, port=5000)
