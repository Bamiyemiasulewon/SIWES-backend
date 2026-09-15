from flask import Blueprint

from .auth_routes import auth_bp
from .user_routes import user_bp
from .department_routes import department_bp
from .asset_routes import asset_bp
from .ticket_routes import ticket_bp
from .dashboard_routes import dashboard_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(asset_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(dashboard_bp)
