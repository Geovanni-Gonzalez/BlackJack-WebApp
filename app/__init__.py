def create_app():
    from flask import Flask
    import os

    # Explicitly point to the folders inside app/web
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'web', 'static')
    template_dir = os.path.join(base_dir, 'web', 'templates')

    app = Flask(__name__,
                static_folder=static_dir,
                template_folder=template_dir)

    # Environment-aware configuration (SECRET_KEY, DB URI, etc.)
    from app.config import get_config
    app.config.from_object(get_config())

    # Initialize Extensions
    from flask_session import Session
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from flask_wtf.csrf import CSRFProtect

    Session(app)
    csrf = CSRFProtect(app)
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=app.config.get('RATELIMIT_DEFAULTS', ["1000 per day", "200 per hour"]),
        storage_uri="memory://"
    )
    app.extensions['limiter'] = limiter

    from app.data.models import db
    db.init_app(app)

    # Register Blueprints
    from app.web.controllers.main import web_bp
    app.register_blueprint(web_bp)

    from app.web.controllers.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.web.controllers.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.web.controllers.sockets import socketio
    socketio.init_app(app)

    with app.app_context():
        db.create_all()

    return app, socketio
