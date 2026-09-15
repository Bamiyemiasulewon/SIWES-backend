from flask import Flask, jsonify
from marshmallow import ValidationError

from config import Config
from .extensions import db, jwt, ma, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.models import User

        user_id = int(jwt_data["sub"])
        return db.session.get(User, user_id)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({"error": "validation_error", "messages": error.messages}), 400

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "not_found", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "internal_server_error", "message": str(error)}), 500

    from app.routes import register_blueprints

    register_blueprints(app)

    return app
