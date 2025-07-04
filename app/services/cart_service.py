from app.models.cart import Cart, CartItem
from app.models.database import db, DBCart, DBCartItem
from app.cache import cache
from typing import Optional
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

class CartService:
    CART_CACHE_PREFIX = "cart:"
    PRODUCT_STATS_KEY = "product_stats"
    TOP_PRODUCTS_KEY = "top_products"
    
    def get_cart(self, user_id: str) -> Cart:
        """Obtener carrito usando patrón Cache-Aside"""
        cache_key = f"{self.CART_CACHE_PREFIX}{user_id}"
        
        # 1. Intentar obtener del caché
        cached_cart = cache.get(cache_key)
        if cached_cart:
            logger.info(f"Carrito {user_id} obtenido del caché")
            items = [CartItem(**item) for item in cached_cart['items']]
            return Cart(user_id=user_id, items=items)
        
        # 2. Si no está en caché, obtener de la base de datos
        logger.info(f"Carrito {user_id} no encontrado en caché, consultando BD")
        db_cart = DBCart.query.filter_by(user_id=user_id).first()
        
        if db_cart:
            items = [
                CartItem(
                    product_id=item.product_id,
                    name=item.name,
                    price=item.price,
                    quantity=item.quantity
                ) for item in db_cart.items
            ]
            cart = Cart(user_id=user_id, items=items)
            
            # 3. Guardar en caché para futuras consultas
            cache.set(cache_key, cart.to_dict())
            logger.info(f"Carrito {user_id} guardado en caché")
            
            return cart
        
        # 4. Si no existe, retornar carrito vacío
        empty_cart = Cart(user_id=user_id, items=[])
        cache.set(cache_key, empty_cart.to_dict())
        return empty_cart
    
    def save_cart(self, cart: Cart) -> None:
        """Guardar carrito en BD y actualizar caché"""
        cache_key = f"{self.CART_CACHE_PREFIX}{cart.user_id}"
        
        try:
            # 1. Guardar en base de datos
            db_cart = DBCart.query.filter_by(user_id=cart.user_id).first()
            if not db_cart:
                db_cart = DBCart(user_id=cart.user_id)
                db.session.add(db_cart)
                db.session.flush()
            
            # Crear diccionario de items existentes para búsqueda rápida
            existing_items = {item.product_id: item for item in db_cart.items}
            new_items = {item.product_id: item for item in cart.items}
            
            # Actualizar o insertar items
            for product_id, cart_item in new_items.items():
                if product_id in existing_items:
                    db_item = existing_items[product_id]
                    db_item.name = cart_item.name
                    db_item.price = cart_item.price
                    db_item.quantity = cart_item.quantity
                else:
                    db_item = DBCartItem(
                        cart_id=db_cart.id,
                        product_id=cart_item.product_id,
                        name=cart_item.name,
                        price=cart_item.price,
                        quantity=cart_item.quantity
                    )
                    db.session.add(db_item)
            
            # Eliminar items que ya no están en el carrito
            for product_id, db_item in existing_items.items():
                if product_id not in new_items:
                    db.session.delete(db_item)
            
            db.session.commit()
            
            # 2. Actualizar caché
            cache.set(cache_key, cart.to_dict())
            logger.info(f"Carrito {cart.user_id} guardado en BD y caché")
            
            # 3. Actualizar estadísticas de productos
            self._update_product_stats(cart)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error guardando carrito {cart.user_id}: {e}")
            raise
    
    def add_item(self, user_id: str, item_data: dict) -> Cart:
        """Agregar item al carrito"""
        cart = self.get_cart(user_id)
        new_item = CartItem(**item_data)
        cart.add_item(new_item)
        self.save_cart(cart)
        
        # Invalidar caché de top productos
        cache.delete(self.TOP_PRODUCTS_KEY)
        
        return cart
    
    def remove_item(self, user_id: str, product_id: int) -> Cart:
        """Eliminar item del carrito"""
        cart = self.get_cart(user_id)
        cart.remove_item(product_id)
        self.save_cart(cart)
        
        # Invalidar caché de top productos
        cache.delete(self.TOP_PRODUCTS_KEY)
        
        return cart
    
    def update_quantity(self, user_id: str, product_id: int, quantity: int) -> Optional[Cart]:
        """Actualizar cantidad de un item"""
        cart = self.get_cart(user_id)
        if cart.update_quantity(product_id, quantity):
            self.save_cart(cart)
            
            # Invalidar caché de top productos
            cache.delete(self.TOP_PRODUCTS_KEY)
            
            return cart
        return None
    
    def clear_cart(self, user_id: str) -> None:
        """Limpiar carrito"""
        cache_key = f"{self.CART_CACHE_PREFIX}{user_id}"
        
        # Eliminar de base de datos
        db_cart = DBCart.query.filter_by(user_id=user_id).first()
        if db_cart:
            db.session.delete(db_cart)
            db.session.commit()
        
        # Eliminar del caché
        cache.delete(cache_key)
        logger.info(f"Carrito {user_id} eliminado")
    
    def _update_product_stats(self, cart: Cart) -> None:
        """Actualizar estadísticas de productos en Redis"""
        try:
            for item in cart.items:
                stats_key = f"{self.PRODUCT_STATS_KEY}:{item.product_id}"
                cache.increment(stats_key, item.quantity)
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def get_top_products(self, limit: int = 10) -> list:
        """Obtener top productos más comprados usando caché"""
        
        # 1. Intentar obtener del caché
        cached_top = cache.get(self.TOP_PRODUCTS_KEY)
        if cached_top:
            logger.info("Top productos obtenido del caché")
            return cached_top[:limit]
        
        # 2. Si no está en caché, calcular desde BD
        logger.info("Top productos no encontrado en caché, calculando desde BD")
        
        try:
            # Consulta para obtener productos más comprados
            top_products_query = db.session.query(
                DBCartItem.product_id,
                DBCartItem.name,
                func.sum(DBCartItem.quantity).label('total_quantity'),
                func.count(DBCartItem.id).label('times_ordered'),
                func.avg(DBCartItem.price).label('avg_price')
            ).group_by(
                DBCartItem.product_id, 
                DBCartItem.name
            ).order_by(
                func.sum(DBCartItem.quantity).desc()
            ).limit(limit * 2)  # Obtener más para el caché
            
            results = top_products_query.all()
            
            top_products = []
            for result in results:
                top_products.append({
                    'product_id': result.product_id,
                    'name': result.name,
                    'total_quantity': int(result.total_quantity),
                    'times_ordered': result.times_ordered,
                    'avg_price': float(result.avg_price)
                })
            
            # 3. Guardar en caché por 10 minutos
            cache.set(self.TOP_PRODUCTS_KEY, top_products, expiration=600)
            logger.info("Top productos calculado y guardado en caché")
            
            return top_products[:limit]
            
        except Exception as e:
            logger.error(f"Error calculando top productos: {e}")
            return []
    
    def get_cache_stats(self) -> dict:
        """Obtener estadísticas del caché"""
        return cache.get_stats()