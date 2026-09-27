from flask import Flask, jsonify, redirect, render_template_string
from flask_jwt_extended import JWTManager
from flask_smorest import Api
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
    api = Api(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.models import User

        user_id = int(jwt_data["sub"])
        return db.session.get(User, user_id)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token_expired", "message": "Token has expired", "status_code": 401}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "invalid_token", "message": "Invalid token", "status_code": 401}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({"error": "unauthorized", "message": "Missing or invalid authorization token", "status_code": 401}), 401

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({"error": "validation_error", "message": "Validation failed", "status_code": 400, "details": error.messages}), 400

    @app.errorhandler(400)
    def handle_bad_request(_error):
        return jsonify({"error": "bad_request", "message": "Bad request", "status_code": 400}), 400

    @app.errorhandler(403)
    def handle_forbidden(_error):
        return jsonify({"error": "forbidden", "message": "Access denied", "status_code": 403}), 403

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "not_found", "message": "Resource not found", "status_code": 404}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return jsonify({"error": "method_not_allowed", "message": "HTTP method not allowed", "status_code": 405}), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "internal_server_error", "message": str(error), "status_code": 500}), 500

    @app.route("/docs")
    def docs_redirect():
        return redirect("/docs/swagger-ui")

    @app.route("/docs/openapi.json")
    def openapi_json():
        return jsonify(api.spec.to_dict())

    @app.route("/docs/swagger-ui")
    def swagger_ui():
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart IT Helpdesk API Docs</title>
            <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
            <style>
                body { margin: 0; background: #f5f7fb; }
                #app { max-width: 1280px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div id="app"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
            <script>
                SwaggerUIBundle({
                    url: '/docs/openapi.json',
                    dom_id: '#app',
                    deepLinking: true,
                    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.Snapshot]
                });
            </script>
        </body>
        </html>
        ''')

    @app.route("/docs/redoc")
    def redoc_ui():
        return redirect("https://redocly.github.io/redoc/?url=/docs/openapi.json")

    from app.routes import register_blueprints

    register_blueprints(api)

    return app
