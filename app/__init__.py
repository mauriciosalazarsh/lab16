from flask import Flask
from app.routes.cart_routes import cart_bp
from app.models.database import db
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar SQLAlchemy
    db.init_app(app)
    
    # Crear todas las tablas
    with app.app_context():
        db.create_all()
    
    app.register_blueprint(cart_bp, url_prefix='/cart')
    return app