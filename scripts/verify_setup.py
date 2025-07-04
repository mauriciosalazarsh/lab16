#!/usr/bin/env python3
"""
Script para verificar que toda la configuración del laboratorio esté funcionando correctamente.
"""

import sys
import os
import requests
import time
import json

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cache import cache
from app.models.database import db, DBCart, DBCartItem
from app import create_app

class SetupVerifier:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.errors = []
        self.warnings = []
        
    def log_error(self, message):
        """Registrar un error"""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message):
        """Registrar una advertencia"""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def log_success(self, message):
        """Registrar un éxito"""
        print(f"✅ {message}")
    
    def check_redis_connections(self):
        """Verificar conexiones a Redis"""
        print("\n🔄 Verificando conexiones a Redis...")
        
        try:
            # Verificar master
            cache.master.ping()
            self.log_success("Redis Master conectado")
            
            # Verificar slaves
            connected_slaves = 0
            for i, slave in enumerate(cache.slaves):
                try:
                    if slave != cache.master:  # No contar el master como slave
                        slave.ping()
                        connected_slaves += 1
                        self.log_success(f"Redis Slave {i+1} conectado")
                except Exception as e:
                    self.log_warning(f"Redis Slave {i+1} no disponible: {e}")
            
            if connected_slaves == 0:
                self.log_warning("No hay slaves de Redis disponibles, usando solo master")
            elif connected_slaves < 2:
                self.log_warning(f"Solo {connected_slaves}/2 slaves disponibles")
            else:
                self.log_success("Todos los slaves de Redis conectados")
                
        except Exception as e:
            self.log_error(f"No se puede conectar a Redis Master: {e}")
    
    def check_database_connection(self):
        """Verificar conexión a PostgreSQL"""
        print("\n🗄️  Verificando conexión a PostgreSQL...")
        
        try:
            app = create_app()
            with app.app_context():
                # Probar conexión con una consulta simple
                db.session.execute('SELECT 1')
                self.log_success("PostgreSQL conectado")
                
                # Verificar tablas
                tables = db.engine.table_names()
                if 'carts' in tables and 'cart_items' in tables:
                    self.log_success("Tablas de base de datos creadas")
                else:
                    self.log_error("Tablas de base de datos no encontradas")
                
        except Exception as e:
            self.log_error(f"No se puede conectar a PostgreSQL: {e}")
    
    def check_test_data(self):
        """Verificar datos de prueba"""
        print("\n📊 Verificando datos de prueba...")
        
        try:
            app = create_app()
            with app.app_context():
                cart_count = DBCart.query.count()
                item_count = DBCartItem.query.count()
                
                if cart_count >= 20:
                    self.log_success(f"Datos de prueba OK: {cart_count} carritos, {item_count} items")
                elif cart_count > 0:
                    self.log_warning(f"Pocos datos de prueba: {cart_count} carritos (se requieren ≥20)")
                else:
                    self.log_error("No hay datos de prueba. Ejecuta: python -m scripts.seed_data")
                    
        except Exception as e:
            self.log_error(f"Error verificando datos de prueba: {e}")
    
    def check_api_endpoints(self):
        """Verificar endpoints de la API"""
        print("\n🌐 Verificando endpoints de la API...")
        
        # Esperar a que la API esté disponible
        max_retries = 10
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    break
            except:
                if attempt < max_retries - 1:
                    print(f"   Esperando API... intento {attempt + 1}/{max_retries}")
                    time.sleep(1)
                else:
                    self.log_error("API no disponible. Asegúrate de ejecutar: python run.py")
                    return
        
        # Probar endpoints principales
        endpoints_to_test = [
            ("GET", "/health", "Health check general"),
            ("GET", "/cart/health", "Health check del carrito"),
            ("GET", "/cart/user001", "Obtener carrito"),
            ("GET", "/cart/stats/top-products", "Top productos"),
            ("GET", "/cart/stats/cache", "Estadísticas de caché")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    self.log_success(f"{description}: {response.status_code}")
                else:
                    self.log_warning(f"{description}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_error(f"{description}: {e}")
    
    def test_cache_functionality(self):
        """Probar funcionalidad del caché"""
        print("\n💾 Probando funcionalidad del caché...")
        
        try:
            # Probar operaciones básicas del caché
            test_key = "test:verification"
            test_value = {"test": True, "timestamp": time.time()}
            
            # Set
            if cache.set(test_key, test_value, expiration=60):
                self.log_success("Cache SET funcionando")
            else:
                self.log_error("Cache SET falló")
                return
            
            # Get
            retrieved_value = cache.get(test_key)
            if retrieved_value and retrieved_value.get("test") == True:
                self.log_success("Cache GET funcionando")
            else:
                self.log_error("Cache GET falló")
                return
            
            # Delete
            if cache.delete(test_key):
                self.log_success("Cache DELETE funcionando")
            else:
                self.log_error("Cache DELETE falló")
            
            # Verificar que fue eliminado
            if not cache.get(test_key):
                self.log_success("Caché funcionando correctamente")
            else:
                self.log_warning("Cache DELETE no eliminó la clave")
                
        except Exception as e:
            self.log_error(f"Error probando caché: {e}")
    
    def test_cache_aside_pattern(self):
        """Probar patrón Cache-Aside"""
        print("\n🔄 Probando patrón Cache-Aside...")
        
        try:
            # Limpiar caché del usuario de prueba
            test_user = "verification_user"
            cache.delete(f"cart:{test_user}")
            
            # Primera consulta (debería ir a BD)
            start_time = time.time()
            response1 = requests.get(f"{self.base_url}/cart/{test_user}")
            time1 = (time.time() - start_time) * 1000
            
            if response1.status_code == 200:
                self.log_success(f"Primera consulta (BD): {time1:.2f}ms")
                
                # Segunda consulta (debería venir del caché)
                start_time = time.time()
                response2 = requests.get(f"{self.base_url}/cart/{test_user}")
                time2 = (time.time() - start_time) * 1000
                
                if response2.status_code == 200:
                    self.log_success(f"Segunda consulta (caché): {time2:.2f}ms")
                    
                    if time2 < time1:
                        improvement = ((time1 - time2) / time1) * 100
                        self.log_success(f"Cache-Aside funcionando: {improvement:.1f}% más rápido")
                    else:
                        self.log_warning("La segunda consulta no fue más rápida")
                else:
                    self.log_error("Segunda consulta falló")
            else:
                self.log_error("Primera consulta falló")
                
        except Exception as e:
            self.log_error(f"Error probando Cache-Aside: {e}")
    
    def check_docker_services(self):
        """Verificar servicios Docker"""
        print("\n🐳 Verificando servicios Docker...")
        
        try:
            import subprocess
            
            # Verificar que Docker Compose esté corriendo
            result = subprocess.run(
                ["docker-compose", "ps"], 
                capture_output=True, 
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            
            if result.returncode == 0:
                output = result.stdout
                services = ['redis-master', 'redis-slave1', 'redis-slave2', 'postgres-ecommerce']
                
                for service in services:
                    if service in output and 'Up' in output:
                        self.log_success(f"Servicio {service} activo")
                    else:
                        self.log_warning(f"Servicio {service} no encontrado o inactivo")
            else:
                self.log_warning("No se puede verificar Docker Compose (puede que no esté instalado)")
                
        except Exception as e:
            self.log_warning(f"Error verificando Docker: {e}")
    
    def generate_summary(self):
        """Generar resumen de la verificación"""
        print("\n" + "="*70)
        print("📋 RESUMEN DE VERIFICACIÓN")
        print("="*70)
        
        if not self.errors and not self.warnings:
            print("🎉 ¡PERFECTO! Todo está configurado correctamente.")
            print("   El laboratorio está listo para ser evaluado.")
        elif not self.errors:
            print("✅ BUENO: La configuración básica está funcionando.")
            print(f"   Hay {len(self.warnings)} advertencias menores.")
        else:
            print("❌ PROBLEMAS ENCONTRADOS:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   • Errores: {len(self.errors)}")
        print(f"   • Advertencias: {len(self.warnings)}")
        print(f"   • Estado: {'✅ LISTO' if not self.errors else '❌ REQUIERE ATENCIÓN'}")

def main():
    print("🔍 VERIFICANDO CONFIGURACIÓN DEL LABORATORIO 16")
    print("=" * 50)
    
    verifier = SetupVerifier()
    
    # Ejecutar todas las verificaciones
    verifier.check_docker_services()
    verifier.check_redis_connections()
    verifier.check_database_connection()
    verifier.check_test_data()
    verifier.check_api_endpoints()
    verifier.test_cache_functionality()
    verifier.test_cache_aside_pattern()
    
    # Generar resumen
    verifier.generate_summary()
    
    return len(verifier.errors) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)