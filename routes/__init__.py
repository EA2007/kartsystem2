from .auth      import auth_bp
from .customers import customers_bp
from .areas     import areas_bp
from .users     import users_bp
from .presence  import presence_bp
from .activity  import activity_bp

all_blueprints = [auth_bp, customers_bp, areas_bp, users_bp, presence_bp, activity_bp]
