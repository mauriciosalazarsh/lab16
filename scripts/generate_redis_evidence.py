#!/usr/bin/env python3
"""
Script simple para generar evidencias Redis sin emojis
"""

import redis
import json
import time
import subprocess
from datetime import datetime

def generate_redis_evidence():
    master = redis.Redis(host='localhost', port=6379, decode_responses=True)
    slave1 = redis.Redis(host='localhost', port=6380, decode_responses=True)
    slave2 = redis.Redis(host='localhost', port=6381, decode_responses=True)
    
    # Generar evidencias de configuración Docker
    print("EVIDENCIAS DE REPLICACION REDIS PARA LATEX")
    print("=" * 50)
    print()
    
    # 1. Configuración Docker
    print("1. CONFIGURACION DOCKER")
    print("-" * 25)
    try:
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        print(result.stdout)
    except:
        print("Error obteniendo estado Docker")
    print()
    
    # 2. Estado de replicación
    print("2. ESTADO DE REPLICACION")
    print("-" * 25)
    
    try:
        # Master info
        master_info = master.info('replication')
        print(f"Master (localhost:6379):")
        print(f"  Role: {master_info.get('role')}")
        print(f"  Connected slaves: {master_info.get('connected_slaves')}")
        print(f"  Replication ID: {master_info.get('master_replid')}")
        print(f"  Offset: {master_info.get('master_repl_offset')}")
        print()
        
        # Slave1 info
        slave1_info = slave1.info('replication')
        print(f"Slave1 (localhost:6380):")
        print(f"  Role: {slave1_info.get('role')}")
        print(f"  Master: {slave1_info.get('master_host')}:{slave1_info.get('master_port')}")
        print(f"  Link status: {slave1_info.get('master_link_status')}")
        print(f"  Last IO: {slave1_info.get('master_last_io_seconds_ago')}s ago")
        print(f"  Offset: {slave1_info.get('slave_repl_offset')}")
        print()
        
        # Slave2 info
        slave2_info = slave2.info('replication')
        print(f"Slave2 (localhost:6381):")
        print(f"  Role: {slave2_info.get('role')}")
        print(f"  Master: {slave2_info.get('master_host')}:{slave2_info.get('master_port')}")
        print(f"  Link status: {slave2_info.get('master_link_status')}")
        print(f"  Last IO: {slave2_info.get('master_last_io_seconds_ago')}s ago")
        print(f"  Offset: {slave2_info.get('slave_repl_offset')}")
        print()
        
    except Exception as e:
        print(f"Error obteniendo replicacion: {e}")
    
    # 3. Distribución de datos
    print("3. DISTRIBUCION DE DATOS")
    print("-" * 25)
    
    try:
        # Escribir datos de prueba
        test_data = {
            'test_key_1': 'Evidencia de replicacion 1',
            'test_key_2': 'Evidencia de replicacion 2',
            'test_key_3': 'Evidencia de replicacion 3',
            'test_key_4': 'Evidencia de replicacion 4',
            'test_key_5': 'Evidencia de replicacion 5'
        }
        
        print("Escribiendo datos en Master:")
        for key, value in test_data.items():
            master.setex(key, 300, value)
            print(f"  {key}: {value}")
        print()
        
        # Esperar replicación
        print("Esperando replicacion (2 segundos)...")
        time.sleep(2)
        
        # Verificar en todos los nodos
        connections = [
            ('Master', master),
            ('Slave1', slave1),
            ('Slave2', slave2)
        ]
        
        for node_name, connection in connections:
            print(f"{node_name}:")
            found_keys = 0
            for key in test_data.keys():
                try:
                    value = connection.get(key)
                    if value:
                        print(f"  {key}: ENCONTRADO")
                        found_keys += 1
                    else:
                        print(f"  {key}: NO ENCONTRADO")
                except Exception as e:
                    print(f"  {key}: ERROR - {e}")
            
            # Estadísticas del nodo
            try:
                info = connection.info()
                total_keys = connection.dbsize()
                memory = info.get('used_memory_human', 'N/A')
                print(f"  Keys found: {found_keys}/5")
                print(f"  Total keys in DB: {total_keys}")
                print(f"  Memory used: {memory}")
                print()
            except Exception as e:
                print(f"  Error obteniendo estadisticas: {e}")
                print()
        
        # Limpiar datos de prueba
        for key in test_data.keys():
            master.delete(key)
            
    except Exception as e:
        print(f"Error en distribucion de datos: {e}")
    
    # 4. Rendimiento
    print("4. RENDIMIENTO")
    print("-" * 25)
    
    try:
        # Escritura en Master
        print("Escribiendo 50 operaciones en Master...")
        write_times = []
        for i in range(50):
            start = time.time()
            master.set(f'perf_{i}', f'value_{i}')
            write_times.append((time.time() - start) * 1000)
        
        avg_write = sum(write_times) / len(write_times)
        print(f"Escritura Master: {avg_write:.2f}ms promedio")
        
        # Lectura en Slaves
        time.sleep(1)  # Esperar replicación
        
        for slave_name, connection in [('Slave1', slave1), ('Slave2', slave2)]:
            read_times = []
            for i in range(50):
                start = time.time()
                connection.get(f'perf_{i}')
                read_times.append((time.time() - start) * 1000)
            
            avg_read = sum(read_times) / len(read_times)
            print(f"Lectura {slave_name}: {avg_read:.2f}ms promedio")
        
        # Limpiar datos de prueba
        for i in range(50):
            master.delete(f'perf_{i}')
            
    except Exception as e:
        print(f"Error en rendimiento: {e}")
    
    print()
    print("=" * 50)
    print("EVIDENCIAS GENERADAS")
    print("Copia el contenido anterior para tu documento LaTeX")

if __name__ == '__main__':
    generate_redis_evidence()