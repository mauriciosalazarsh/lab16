from flask import Blueprint, jsonify, request
from app.services.cart_service import CartService
import time
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

cart_bp = Blueprint('cart', __name__)
cart_service = CartService()

@cart_bp.route('/<user_id>', methods=['GET'])
def get_cart(user_id):
    """Obtener carrito de un usuario"""
    start_time = time.time()
    try:
        cart = cart_service.get_cart(user_id)
        response_time = (time.time() - start_time) * 1000  # en milisegundos
        
        response = cart.to_dict()
        response['_metadata'] = {
            'response_time_ms': round(response_time, 2),
            'source': 'cache_or_db'
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error obteniendo carrito {user_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@cart_bp.route('/<user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    """Agregar item al carrito"""
    start_time = time.time()
    try:
        item_data = request.json
        
        # Validar datos requeridos
        required_fields = ['product_id', 'name', 'price', 'quantity']
        if not all(field in item_data for field in required_fields):
            return jsonify({'error': 'Campos requeridos: product_id, name, price, quantity'}), 400
        
        cart = cart_service.add_item(user_id, item_data)
        response_time = (time.time() - start_time) * 1000
        
        return jsonify({
            'message': 'Item agregado exitosamente',
            'cart': cart.to_dict(),
            '_metadata': {
                'response_time_ms': round(response_time, 2)
            }
        })
    except Exception as e:
        logger.error(f"Error agregando item al carrito {user_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@cart_bp.route('/<user_id>/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(user_id, product_id):
    """Eliminar item del carrito"""
    start_time = time.time()
    try:
        cart = cart_service.remove_item(user_id, product_id)
        response_time = (time.time() - start_time) * 1000
        
        return jsonify({
            'message': 'Item eliminado exitosamente',
            'cart': cart.to_dict(),
            '_metadata': {
                'response_time_ms': round(response_time, 2)
            }
        })
    except Exception as e:
        logger.error(f"Error eliminando item del carrito {user_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@cart_bp.route('/<user_id>/update/<int:product_id>', methods=['PUT'])
def update_quantity(user_id, product_id):
    """Actualizar cantidad de un item"""
    start_time = time.time()
    try:
        quantity = request.json.get('quantity')
        
        if not isinstance(quantity, int) or quantity < 0:
            return jsonify({'error': 'La cantidad debe ser un número entero positivo'}), 400
        
        cart = cart_service.update_quantity(user_id, product_id, quantity)
        response_time = (time.time() - start_time) * 1000
        
        if cart:
            return jsonify({
                'message': 'Cantidad actualizada exitosamente',
                'cart': cart.to_dict(),
                '_metadata': {
                    'response_time_ms': round(response_time, 2)
                }
            })
        return jsonify({'error': 'Producto no encontrado en el carrito'}), 404
    except Exception as e:
        logger.error(f"Error actualizando cantidad en carrito {user_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@cart_bp.route('/<user_id>/clear', methods=['POST'])
def clear_cart(user_id):
    """Limpiar carrito"""
    start_time = time.time()
    try:
        cart_service.clear_cart(user_id)
        response_time = (time.time() - start_time) * 1000
        
        return jsonify({
            'message': 'Carrito limpiado exitosamente',
            '_metadata': {
                'response_time_ms': round(response_time, 2)
            }
        })
    except Exception as e:
        logger.error(f"Error limpiando carrito {user_id}: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# Nuevos endpoints para estadísticas

@cart_bp.route('/stats/top-products', methods=['GET'])
def get_top_products():
    """Obtener top 10 productos más comprados"""
    start_time = time.time()
    try:
        limit = int(request.args.get('limit', 10))
        if limit > 50:  # Límite máximo
            limit = 50
        
        top_products = cart_service.get_top_products(limit)
        response_time = (time.time() - start_time) * 1000
        
        return jsonify({
            'top_products': top_products,
            'total_count': len(top_products),
            '_metadata': {
                'response_time_ms': round(response_time, 2),
                'limit': limit
            }
        })
    except Exception as e:
        logger.error(f"Error obteniendo top productos: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@cart_bp.route('/stats/cache', methods=['GET'])
def get_cache_stats():
    """Obtener estadísticas del caché Redis"""
    try:
        stats = cart_service.get_cache_stats()
        return jsonify({
            'cache_stats': stats,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de caché: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@cart_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del servicio"""
    try:
        # Verificar conexión a BD haciendo una consulta simple
        from app.models.database import db
        db.session.execute(text('SELECT 1'))
        
        # Verificar conexión a Redis
        cache_stats = cart_service.get_cache_stats()
        redis_healthy = cache_stats['master']['status'] == 'connected'
        
        return jsonify({
            'status': 'healthy' if redis_healthy else 'degraded',
            'database': 'connected',
            'redis_master': cache_stats['master']['status'],
            'redis_slaves': [slave.get('status', 'unknown') for slave in cache_stats['slaves']],
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500
    

@cart_bp.route('/general-health', methods=['GET'])  
def general_health():
    """Health check general"""
    return jsonify({'status': 'ok', 'service': 'ecommerce-cart'})