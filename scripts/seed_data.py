from app import create_app
from app.models.database import db, DBCart, DBCartItem
from datetime import datetime, timezone
import random

def seed_database():
    app = create_app()
    
    with app.app_context():
        # Limpiar datos existentes
        DBCartItem.query.delete()
        DBCart.query.delete()
        
        # Lista de productos realistas para el ecommerce
        products = [
            {"name": "Laptop Dell XPS 13", "price_range": (800, 1500)},
            {"name": "Mouse Inalámbrico Logitech", "price_range": (25, 80)},
            {"name": "Teclado Mecánico RGB", "price_range": (60, 200)},
            {"name": "Monitor 27\" 4K", "price_range": (250, 600)},
            {"name": "Audífonos Bluetooth Sony", "price_range": (100, 350)},
            {"name": "Webcam HD 1080p", "price_range": (40, 120)},
            {"name": "SSD 1TB Samsung", "price_range": (80, 150)},
            {"name": "Memoria RAM 16GB DDR4", "price_range": (60, 120)},
            {"name": "Tarjeta Gráfica RTX 4060", "price_range": (300, 500)},
            {"name": "Smartphone iPhone 15", "price_range": (700, 1200)},
            {"name": "Tablet iPad Air", "price_range": (400, 800)},
            {"name": "Smartwatch Apple Watch", "price_range": (200, 500)},
            {"name": "Parlante Bluetooth JBL", "price_range": (50, 200)},
            {"name": "Cargador Inalámbrico", "price_range": (20, 60)},
            {"name": "Hub USB-C 7 en 1", "price_range": (30, 80)},
            {"name": "Cable HDMI 4K", "price_range": (15, 40)},
            {"name": "Mousepad Gaming XXL", "price_range": (20, 50)},
            {"name": "Luz LED para Escritorio", "price_range": (25, 75)},
            {"name": "Soporte para Laptop", "price_range": (30, 100)},
            {"name": "Funda para Laptop 15\"", "price_range": (15, 45)},
            {"name": "Micrófono USB Profesional", "price_range": (80, 250)},
            {"name": "Cámara Web 4K", "price_range": (120, 300)},
            {"name": "Router WiFi 6", "price_range": (100, 300)},
            {"name": "Disco Duro Externo 2TB", "price_range": (70, 150)},
            {"name": "Impresora Multifuncional", "price_range": (150, 400)},
            {"name": "Escáner de Documentos", "price_range": (100, 250)},
            {"name": "Ups/Regulador 750VA", "price_range": (80, 180)},
            {"name": "Switch Ethernet 8 Puertos", "price_range": (25, 80)},
            {"name": "Proyector HD Portátil", "price_range": (200, 600)},
            {"name": "Silla Gaming Ergonómica", "price_range": (150, 500)},
            {"name": "Escritorio Gaming RGB", "price_range": (200, 800)},
            {"name": "Cooler para CPU", "price_range": (30, 120)},
            {"name": "Fuente de Poder 750W", "price_range": (80, 200)},
            {"name": "Gabinete Gaming RGB", "price_range": (60, 200)},
            {"name": "Ventiladores RGB 120mm (3 Pack)", "price_range": (40, 100)},
            {"name": "Tarjeta de Sonido Externa", "price_range": (50, 150)},
            {"name": "Adaptador WiFi USB", "price_range": (15, 50)},
            {"name": "Kit de Herramientas PC", "price_range": (20, 60)},
            {"name": "Cable de Red Cat6 (5m)", "price_range": (10, 25)},
            {"name": "Limpiador de Pantallas", "price_range": (8, 20)}
        ]
        
        # Crear 25 carritos de prueba
        test_carts = []
        
        for i in range(1, 26):  # 25 carritos
            user_id = f"user{i:03d}"  # user001, user002, etc.
            
            # Cada carrito tendrá entre 3 y 10 items
            num_items = random.randint(3, 10)
            
            # Seleccionar productos únicos para este carrito
            selected_products = random.sample(products, num_items)
            
            cart_items = []
            for j, product in enumerate(selected_products):
                # Generar precio dentro del rango del producto
                price = round(random.uniform(product["price_range"][0], product["price_range"][1]), 2)
                
                # Cantidad entre 1 y 5
                quantity = random.randint(1, 5)
                
                cart_items.append({
                    'product_id': (i - 1) * 10 + j + 1,  # IDs únicos
                    'name': product["name"],
                    'price': price,
                    'quantity': quantity
                })
            
            test_carts.append({
                'user_id': user_id,
                'items': cart_items
            })
        
        # Insertar datos en la base de datos
        total_carts = 0
        total_items = 0
        
        for cart_data in test_carts:
            # Crear el carrito
            cart = DBCart(
                user_id=cart_data['user_id'],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(cart)
            db.session.flush()  # Para obtener el ID del carrito
            
            # Agregar items al carrito
            for item_data in cart_data['items']:
                item = DBCartItem(
                    cart_id=cart.id,
                    product_id=item_data['product_id'],
                    name=item_data['name'],
                    price=item_data['price'],
                    quantity=item_data['quantity'],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.session.add(item)
                total_items += 1
            
            total_carts += 1
        
        # Confirmar todos los cambios
        db.session.commit()
        
        # Mostrar estadísticas
        print("✅ Datos de prueba insertados correctamente")
        print(f"📊 Estadísticas:")
        print(f"   • Carritos creados: {total_carts}")
        print(f"   • Items totales: {total_items}")
        print(f"   • Promedio de items por carrito: {total_items/total_carts:.1f}")
        
        # Mostrar algunos ejemplos
        print(f"\n📋 Ejemplos de carritos creados:")
        for i, cart_data in enumerate(test_carts[:3]):  # Mostrar solo los primeros 3
            total_value = sum(item['price'] * item['quantity'] for item in cart_data['items'])
            print(f"   {cart_data['user_id']}: {len(cart_data['items'])} items, Total: ${total_value:.2f}")
        
        if len(test_carts) > 3:
            print(f"   ... y {len(test_carts) - 3} carritos más")

if __name__ == '__main__':
    seed_database()