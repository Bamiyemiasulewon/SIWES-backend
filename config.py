import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/smart_it_helpdesk",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "this-is-a-very-long-jwt-secret-key-for-test-usage")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False
    API_TITLE = "Smart IT Helpdesk API"
    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.1.0"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_JSON_URL = "/docs/openapi.json"
    OPENAPI_REDOC_URL = "/docs/redoc"
    OPENAPI_SWAGGER_UI_URL = "/docs/swagger-ui"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
