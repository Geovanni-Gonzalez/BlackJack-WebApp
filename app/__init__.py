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
    
    # Security & Session Config
    app.config['SECRET_KEY'] = 'dev-key-change-in-prod-8823'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    
    # DB Config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blackjack.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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
        default_limits=["1000 per day", "200 per hour"],
        storage_uri="memory://"
    )
    
    # Make extensions available to other modules if needed (e.g. limiter)
    app.extensions['limiter'] = limiter

    from app.web.models import db
    db.init_app(app)
    
    # Register Blueprints
    from app.web import web_bp
    app.register_blueprint(web_bp)

    from app.web.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Register API Blueprint (Deferred import to avoid circular dependency)
    from app.web.api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize SocketIO (Import here to avoid circular imports)
    from app.web.sockets import socketio
    socketio.init_app(app)

    with app.app_context():
        db.create_all()

    return app, socketio
