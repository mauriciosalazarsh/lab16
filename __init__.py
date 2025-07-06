from flask import Flask, jsonify
import logging
import os
from app.routes.cart_routes import cart_bp
from app.models.database import db
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Inicializar SQLAlchemy
    db.init_app(app)
    
    # Crear todas las tablas
    with app.app_context():
        db.create_all()
    
    # Registrar blueprints
    app.register_blueprint(cart_bp, url_prefix='/cart')
    
    # Ruta de salud general
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'ecommerce-cart'})
    
    # Ruta principal
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Ecommerce Cart API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'cart_health': '/cart/health',
                'get_cart': '/cart/<user_id>',
                'add_item': '/cart/<user_id>/add',
                'remove_item': '/cart/<user_id>/remove/<product_id>',
                'update_quantity': '/cart/<user_id>/update/<product_id>',
                'clear_cart': '/cart/<user_id>/clear',
                'top_products': '/cart/stats/top-products',
                'cache_stats': '/cart/stats/cache'
            }
        })
    
    return app