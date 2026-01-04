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
    
    # Register Blueprints
    from app.web import web_bp
    app.register_blueprint(web_bp)
    
    return app
