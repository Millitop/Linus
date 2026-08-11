"""Application factory."""
import os

from flask import Flask

from app.extensions import csrf, db, limiter, login_manager, migrate
from config import CONFIG_BY_NAME


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_CONFIG", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(CONFIG_BY_NAME[config_name])

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.models import StaffUser

    @login_manager.user_loader
    def load_staff_user(user_id: str):
        return db.session.get(StaffUser, int(user_id))

    from app.admin.routes import admin_bp
    from app.auth.routes import auth_bp
    from app.card.routes import card_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(card_bp)

    @app.route("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("admin.dashboard"))

    @app.context_processor
    def inject_site_name():
        return {"site_name": app.config["SITE_NAME"]}

    return app
