import requests
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Agregar el directorio padre al path para importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cache import cache

class PerformanceTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            'cache_enabled': {
                'get_cart': [],
                'add_item': [],
                'top_products': []
            },
            'cache_disabled': {
                'get_cart': [],
                'add_item': [],
                'top_products': []
            }
        }
    
    def clear_cache(self):
        """Limpiar todo el caché de Redis"""
        try:
            cache.master.flushall()
            print("✅ Caché limpiado")
        except Exception as e:
            print(f"❌ Error limpiando caché: {e}")
    
    def measure_request_time(self, method, url, **kwargs):
        """Medir tiempo de respuesta de una petición"""
        start_time = time.time()
        try:
            if method.upper() == 'GET':
                response = requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = requests.put(url, **kwargs)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # en milisegundos
            
            return {
                'response_time': response_time,
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
        except Exception as e:
            end_time = time.time()
            return {
                'response_time': (end_time - start_time) * 1000,
                'status_code': 0,
                'success': False,
                'error': str(e)
            }
    
    def test_get_cart_performance(self, user_ids, num_requests=50):
        """Probar rendimiento de obtener carritos"""
        print(f"\n🔍 Probando GET /cart/<user_id> con {num_requests} peticiones...")
        
        # Test con caché habilitado
        print("  📊 Con caché habilitado:")
        times = []
        for i in range(num_requests):
            user_id = user_ids[i % len(user_ids)]
            result = self.measure_request_time('GET', f"{self.base_url}/cart/{user_id}")
            if result['success']:
                times.append(result['response_time'])
        
        self.results['cache_enabled']['get_cart'] = times
        avg_time = statistics.mean(times) if times else 0
        print(f"    • Tiempo promedio: {avg_time:.2f}ms")
        print(f"    • Peticiones exitosas: {len(times)}/{num_requests}")
        
        # Limpiar caché y probar sin caché
        self.clear_cache()
        print("  📊 Sin caché (primer acceso):")
        times = []
        for i in range(num_requests):
            user_id = user_ids[i % len(user_ids)]
            # Limpiar caché antes de cada petición para simular sin caché
            cache.delete(f"cart:{user_id}")
            result = self.measure_request_time('GET', f"{self.base_url}/cart/{user_id}")
            if result['success']:
                times.append(result['response_time'])
        
        self.results['cache_disabled']['get_cart'] = times
        avg_time = statistics.mean(times) if times else 0
        print(f"    • Tiempo promedio: {avg_time:.2f}ms")
        print(f"    • Peticiones exitosas: {len(times)}/{num_requests}")
    
    def test_add_item_performance(self, user_ids, num_requests=30):
        """Probar rendimiento de agregar items"""
        print(f"\n➕ Probando POST /cart/<user_id>/add con {num_requests} peticiones...")
        
        sample_item = {
            "product_id": 9999,
            "name": "Producto de Prueba",
            "price": 99.99,
            "quantity": 1
        }
        
        # Test con caché
        print("  📊 Con caché habilitado:")
        times = []
        for i in range(num_requests):
            user_id = user_ids[i % len(user_ids)]
            sample_item['product_id'] = 9999 + i  # IDs únicos
            result = self.measure_request_time(
                'POST', 
                f"{self.base_url}/cart/{user_id}/add",
                json=sample_item,
                headers={'Content-Type': 'application/json'}
            )
            if result['success']:
                times.append(result['response_time'])
        
        self.results['cache_enabled']['add_item'] = times
        avg_time = statistics.mean(times) if times else 0
        print(f"    • Tiempo promedio: {avg_time:.2f}ms")
        print(f"    • Peticiones exitosas: {len(times)}/{num_requests}")
    
    def test_top_products_performance(self, num_requests=20):
        """Probar rendimiento del endpoint de top productos"""
        print(f"\n🏆 Probando GET /cart/stats/top-products con {num_requests} peticiones...")
        
        # Test con caché habilitado
        print("  📊 Con caché habilitado:")
        times = []
        for i in range(num_requests):
            result = self.measure_request_time('GET', f"{self.base_url}/cart/stats/top-products")
            if result['success']:
                times.append(result['response_time'])
        
        self.results['cache_enabled']['top_products'] = times
        avg_time = statistics.mean(times) if times else 0
        print(f"    • Tiempo promedio: {avg_time:.2f}ms")
        print(f"    • Peticiones exitosas: {len(times)}/{num_requests}")
        
        # Test sin caché
        cache.delete("top_products")
        print("  📊 Sin caché:")
        times = []
        for i in range(num_requests):
            # Limpiar caché antes de cada petición
            cache.delete("top_products")
            result = self.measure_request_time('GET', f"{self.base_url}/cart/stats/top-products")
            if result['success']:
                times.append(result['response_time'])
        
        self.results['cache_disabled']['top_products'] = times
        avg_time = statistics.mean(times) if times else 0
        print(f"    • Tiempo promedio: {avg_time:.2f}ms")
        print(f"    • Peticiones exitosas: {len(times)}/{num_requests}")
    
    def test_concurrent_requests(self, user_ids, num_threads=10, requests_per_thread=5):
        """Probar rendimiento con peticiones concurrentes"""
        print(f"\n⚡ Probando peticiones concurrentes: {num_threads} hilos, {requests_per_thread} peticiones/hilo")
        
        def make_requests(thread_id):
            times = []
            for i in range(requests_per_thread):
                user_id = user_ids[(thread_id * requests_per_thread + i) % len(user_ids)]
                result = self.measure_request_time('GET', f"{self.base_url}/cart/{user_id}")
                if result['success']:
                    times.append(result['response_time'])
            return times
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_requests, i) for i in range(num_threads)]
            all_times = []
            for future in as_completed(futures):
                all_times.extend(future.result())
        
        total_time = time.time() - start_time
        avg_time = statistics.mean(all_times) if all_times else 0
        
        print(f"    • Tiempo total: {total_time:.2f}s")
        print(f"    • Tiempo promedio por petición: {avg_time:.2f}ms")
        print(f"    • Peticiones por segundo: {len(all_times)/total_time:.2f}")
        print(f"    • Peticiones exitosas: {len(all_times)}/{num_threads * requests_per_thread}")
    
    def generate_report(self):
        """Generar reporte de rendimiento"""
        print("\n" + "="*70)
        print("📈 REPORTE DE RENDIMIENTO")
        print("="*70)
        
        for operation in ['get_cart', 'add_item', 'top_products']:
            if (self.results['cache_enabled'][operation] and 
                self.results['cache_disabled'][operation]):
                
                cache_enabled = self.results['cache_enabled'][operation]
                cache_disabled = self.results['cache_disabled'][operation]
                
                avg_with_cache = statistics.mean(cache_enabled)
                avg_without_cache = statistics.mean(cache_disabled)
                improvement = ((avg_without_cache - avg_with_cache) / avg_without_cache) * 100
                
                print(f"\n🔧 {operation.upper()}:")
                print(f"  Con caché:    {avg_with_cache:.2f}ms (promedio)")
                print(f"  Sin caché:    {avg_without_cache:.2f}ms (promedio)")
                print(f"  Mejora:       {improvement:.1f}% más rápido con caché")
                print(f"  Factor:       {avg_without_cache/avg_with_cache:.1f}x más rápido")
        
        # Estadísticas de Redis
        try:
            redis_stats = cache.get_stats()
            print(f"\n🔄 ESTADÍSTICAS DE REDIS:")
            print(f"  Master: {redis_stats['master']['status']}")
            if redis_stats['master']['status'] == 'connected':
                info = redis_stats['master']['info']
                print(f"    • Clientes conectados: {info.get('connected_clients', 0)}")
                print(f"    • Memoria utilizada: {info.get('used_memory_human', '0')}")
                print(f"    • Cache hits: {info.get('keyspace_hits', 0)}")
                print(f"    • Cache misses: {info.get('keyspace_misses', 0)}")
            
            print(f"  Slaves: {len([s for s in redis_stats['slaves'] if s.get('status') == 'connected'])} activos")
        except Exception as e:
            print(f"  ❌ Error obteniendo estadísticas: {e}")

def main():
    # Verificar que la API esté disponible
    tester = PerformanceTest()
    
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ La API no está disponible. Asegúrate de que esté ejecutándose en localhost:5000")
            return
    except requests.exceptions.RequestException:
        print("❌ No se puede conectar a la API. Asegúrate de que esté ejecutándose en localhost:5000")
        return
    
    print("🚀 Iniciando pruebas de rendimiento...")
    print("⚠️  Asegúrate de tener datos de prueba cargados (ejecuta seed_data.py primero)")
    
    # Lista de usuarios de prueba
    user_ids = [f"user{i:03d}" for i in range(1, 26)]  # user001 a user025
    
    # Ejecutar pruebas
    tester.test_get_cart_performance(user_ids, num_requests=100)
    tester.test_add_item_performance(user_ids, num_requests=50)
    tester.test_top_products_performance(num_requests=30)
    tester.test_concurrent_requests(user_ids, num_threads=10, requests_per_thread=10)
    
    # Generar reporte final
    tester.generate_report()
    
    print("\n✅ Pruebas de rendimiento completadas")

if __name__ == '__main__':
    main()