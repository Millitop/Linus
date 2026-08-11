"""Shared Flask extension instances.

Kept in their own module (rather than app/__init__.py) so blueprints and
models can import them without triggering a circular import on the app
factory.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

login_manager.login_view = "auth.login"
login_manager.login_message = "Logga in för att fortsätta."
login_manager.login_message_category = "warning"
