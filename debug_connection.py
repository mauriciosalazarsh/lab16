#!/usr/bin/env python3
"""
Script para verificar la conexión a PostgreSQL y Redis
"""

import psycopg2
import redis
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config

def test_postgres_connection():
    """Probar conexión a PostgreSQL"""
    print("🔍 Probando conexión a PostgreSQL...")
    
    try:
        # Construir connection string
        conn_string = f"host={Config.POSTGRES_HOST} port={Config.POSTGRES_PORT} dbname={Config.POSTGRES_DB} user={Config.POSTGRES_USER} password={Config.POSTGRES_PASSWORD}"
        print(f"   Connection string: {conn_string}")
        
        # Intentar conectar
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Ejecutar una consulta simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ PostgreSQL conectado exitosamente!")
        print(f"   Versión: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def test_redis_connection():
    """Probar conexión a Redis"""
    print("\n🔍 Probando conexión a Redis...")
    
    try:
        # Probar Redis Master
        r_master = redis.Redis(host=Config.REDIS_MASTER_HOST, port=Config.REDIS_MASTER_PORT, decode_responses=True)
        r_master.ping()
        print(f"✅ Redis Master conectado ({Config.REDIS_MASTER_HOST}:{Config.REDIS_MASTER_PORT})")
        
        # Probar Redis Slaves
        slaves_connected = 0
        for i, (host, port) in enumerate([(Config.REDIS_SLAVE1_HOST, Config.REDIS_SLAVE1_PORT), 
                                          (Config.REDIS_SLAVE2_HOST, Config.REDIS_SLAVE2_PORT)]):
            try:
                r_slave = redis.Redis(host=host, port=port, decode_responses=True)
                r_slave.ping()
                print(f"✅ Redis Slave {i+1} conectado ({host}:{port})")
                slaves_connected += 1
            except Exception as e:
                print(f"❌ Redis Slave {i+1} falló ({host}:{port}): {e}")
        
        print(f"   Slaves conectados: {slaves_connected}/2")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Redis Master: {e}")
        return False

def test_database_creation():
    """Intentar crear la base de datos si no existe"""
    print("\n🔍 Verificando/creando base de datos...")
    
    try:
        # Conectar a PostgreSQL sin especificar base de datos
        conn_string = f"host={Config.POSTGRES_HOST} port={Config.POSTGRES_PORT} user={Config.POSTGRES_USER} password={Config.POSTGRES_PASSWORD}"
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (Config.POSTGRES_DB,))
        if cursor.fetchone():
            print(f"✅ Base de datos '{Config.POSTGRES_DB}' ya existe")
        else:
            # Crear la base de datos
            cursor.execute(f"CREATE DATABASE {Config.POSTGRES_DB}")
            print(f"✅ Base de datos '{Config.POSTGRES_DB}' creada exitosamente")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return False

def show_configuration():
    """Mostrar configuración actual"""
    print("\n📋 Configuración actual:")
    print(f"   PostgreSQL Host: {Config.POSTGRES_HOST}")
    print(f"   PostgreSQL Port: {Config.POSTGRES_PORT}")
    print(f"   PostgreSQL Database: {Config.POSTGRES_DB}")
    print(f"   PostgreSQL User: {Config.POSTGRES_USER}")
    print(f"   Redis Master: {Config.REDIS_MASTER_HOST}:{Config.REDIS_MASTER_PORT}")
    print(f"   Redis Slave 1: {Config.REDIS_SLAVE1_HOST}:{Config.REDIS_SLAVE1_PORT}")
    print(f"   Redis Slave 2: {Config.REDIS_SLAVE2_HOST}:{Config.REDIS_SLAVE2_PORT}")

def main():
    print("🚀 DIAGNÓSTICO DE CONEXIONES")
    print("=" * 50)
    
    show_configuration()
    
    # Probar conexiones
    postgres_ok = test_postgres_connection()
    
    if not postgres_ok:
        print("\n🔧 Intentando crear base de datos...")
        if test_database_creation():
            postgres_ok = test_postgres_connection()
    
    redis_ok = test_redis_connection()
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN:")
    print(f"   PostgreSQL: {'✅ OK' if postgres_ok else '❌ Error'}")
    print(f"   Redis: {'✅ OK' if redis_ok else '❌ Error'}")
    
    if postgres_ok and redis_ok:
        print("\n🎉 ¡Todo listo! Puedes ejecutar la aplicación.")
        return True
    else:
        print("\n⚠️  Revisa los errores anteriores antes de continuar.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)