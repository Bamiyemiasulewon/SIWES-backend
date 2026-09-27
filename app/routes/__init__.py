from .auth_routes import auth_bp
from .user_routes import user_bp
from .department_routes import department_bp
from .asset_routes import asset_bp
from .ticket_routes import ticket_bp
from .dashboard_routes import dashboard_bp


def register_blueprints(api):
    api.register_blueprint(auth_bp)
    api.register_blueprint(user_bp)
    api.register_blueprint(department_bp)
    api.register_blueprint(asset_bp)
    api.register_blueprint(ticket_bp)
    api.register_blueprint(dashboard_bp)
