def create_app():
    from flask import Flask
    app = Flask(__name__)
    
    # Register Blueprints
    from app.web import web_bp
    app.register_blueprint(web_bp)
    
    return app
