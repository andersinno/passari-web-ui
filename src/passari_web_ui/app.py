import logging

import click
from flask import Flask, current_app, g, redirect, request, url_for
from flask.cli import FlaskGroup
from flask_security import (Security, SQLAlchemySessionUserDatastore,
                            current_user)
from flask_wtf.csrf import CSRFProtect

import rq_dashboard
from flask_talisman import Talisman
from passari_web_ui.commands import create_db, init_db
from passari_web_ui.config import get_flask_config
from passari_web_ui.db import db
from passari_web_ui.db.models import Role, User
from passari_web_ui.ui.utils import get_system_status
from passari_workflow.db.connection import get_connection_uri
from passari_workflow.redis.connection import get_redis_url


def add_system_status():
    """
    Add system status information to UI views
    """
    if request.path.startswith("/web-ui"):
        # System status is only displayed in the web UI
        g.system_status = get_system_status()


def require_authentication():
    """
    Check that the user is authenticated
    """
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()


def register_rq_dashboard(app):
    """
    Install RQ dashboard into the web application
    """
    redis_url = get_redis_url()

    app.config.from_object(rq_dashboard.default_settings)
    app.config.from_mapping({"RQ_DASHBOARD_REDIS_URL": [redis_url]})

    # We can't decorate rq_dashboard routes with the 'login_required'
    # decorator, so use a 'before_request' function, which does essentially
    # the same thing
    rq_dashboard.blueprint.before_request(require_authentication)

    # Templates have been overridden in 'templates/rq_dashboard' to provide
    # more seamless integration with the rest of the web UI
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/web-ui/rq")


def init_security():
    """
    Install Flask-Security (used for authentication) into the web application
    """
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    Security(current_app, user_datastore)


def configure_custom_log_levels(log_levels):
    if log_levels:
        if isinstance(log_levels, str):
            log_levels = log_levels.replace(",", " ").split()

        if isinstance(log_levels, list):
            log_levels = dict(x.split(":", 1) for x in log_levels)

        for logger_name, level_name in (log_levels or {}).items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level_name)


def create_app():
    """
    Create the WSGI app for passari-web-ui
    """
    app = Flask("passari_web_ui")

    app.config.from_object("passari_web_ui.default_config")
    app.config.update(**get_flask_config())
    app.config["SQLALCHEMY_DATABASE_URI"] = get_connection_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    configure_custom_log_levels(app.config.get("CUSTOM_LOG_LEVELS"))

    db.init_app(app)

    with app.app_context():
        init_security()

    # Register blueprints
    from passari_web_ui.api.views import routes as api_routes
    from passari_web_ui.ui.views import routes as ui_routes

    api_routes.before_request(require_authentication)
    ui_routes.before_request(require_authentication)

    app.before_request(add_system_status)

    app.register_blueprint(api_routes, url_prefix="/api")
    app.register_blueprint(ui_routes, url_prefix="/web-ui")

    register_rq_dashboard(app)

    # Redirect the user to the main page of web UI by default
    app.add_url_rule("/", "index", lambda: redirect(url_for("ui.overview")))

    # Register CLI commands
    app.cli.add_command(init_db)
    app.cli.add_command(create_db)

    # Enable global CSRF
    CSRFProtect(app)

    # Enable HTTPS only and other security improvements
    Talisman(
        app,
        content_security_policy={
            "default-src": "'self'",
            # 'unsafe-eval' required for compiling Vue templates
            "script-src": "'self' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            # Needed for embedding HTML reports in "View single SIP" page
            "frame-src": "'self' blob:"
        },
        content_security_policy_nonce_in=["script-src"]
    )

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """
    Management script for the Passari Web application.
    """
    pass


if __name__ == "__main__":
    cli()
