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
    
    # DB Config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blackjack.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    from app.web.models import db
    db.init_app(app)
    
    # Register Blueprints
    from app.web import web_bp
    app.register_blueprint(web_bp)
    
    with app.app_context():
        db.create_all()
    
    return app
