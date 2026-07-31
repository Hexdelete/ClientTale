import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db_user = os.environ.get("MYSQL_USER", "clienttale")
    db_password = os.environ.get("MYSQL_PASSWORD", "clienttale")
    db_host = os.environ.get("MYSQL_HOST", "db")
    db_port = os.environ.get("MYSQL_PORT", "3306")
    db_name = os.environ.get("MYSQL_DATABASE", "clienttale")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB upload cap

    db.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.staff import staff_bp
    from app.routes.cases import cases_bp
    from app.routes.events import events_bp
    from app.routes.pdf_import import pdf_import_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(staff_bp, url_prefix="/api/staff")
    app.register_blueprint(cases_bp, url_prefix="/api/cases")
    app.register_blueprint(events_bp, url_prefix="/api")
    app.register_blueprint(pdf_import_bp, url_prefix="/api/import")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
