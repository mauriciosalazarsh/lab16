import redis
import json
import logging
from typing import Optional, Any, List
from app.config import Config

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.master = None
        self.slaves = []
        self.current_slave = 0
        self._connect()
    
    def _connect(self):
        """Conectar a Redis master y slaves"""
        try:
            # Conexión al master (para escrituras)
            self.master = redis.Redis(
                host=Config.REDIS_MASTER_HOST,
                port=Config.REDIS_MASTER_PORT,
                decode_responses=True,
                health_check_interval=30
            )
            self.master.ping()
            logger.info("Conectado a Redis Master")
            
            # Conexiones a slaves (para lecturas)
            slave_configs = [
                (Config.REDIS_SLAVE1_HOST, Config.REDIS_SLAVE1_PORT),
                (Config.REDIS_SLAVE2_HOST, Config.REDIS_SLAVE2_PORT)
            ]
            
            for host, port in slave_configs:
                try:
                    slave = redis.Redis(
                        host=host,
                        port=port,
                        decode_responses=True,
                        health_check_interval=30
                    )
                    slave.ping()
                    self.slaves.append(slave)
                    logger.info(f"Conectado a Redis Slave: {host}:{port}")
                except Exception as e:
                    logger.warning(f"No se pudo conectar al slave {host}:{port}: {e}")
            
            # Si no hay slaves disponibles, usar master para lecturas
            if not self.slaves:
                self.slaves = [self.master]
                logger.info("Usando master para lecturas (no hay slaves disponibles)")
                
        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            raise
    
    def _get_read_connection(self) -> redis.Redis:
        """Obtener conexión para lectura (round-robin entre slaves)"""
        if not self.slaves:
            return self.master
        
        connection = self.slaves[self.current_slave]
        self.current_slave = (self.current_slave + 1) % len(self.slaves)
        return connection
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del caché"""
        try:
            conn = self._get_read_connection()
            value = conn.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo clave {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, expiration: int = None) -> bool:
        """Establecer valor en el caché"""
        try:
            if expiration is None:
                expiration = Config.CACHE_EXPIRATION
            
            serialized_value = json.dumps(value, default=str)
            self.master.setex(key, expiration, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error estableciendo clave {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Eliminar valor del caché"""
        try:
            self.master.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error eliminando clave {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Verificar si existe una clave"""
        try:
            conn = self._get_read_connection()
            return conn.exists(key) > 0
        except Exception as e:
            logger.error(f"Error verificando existencia de {key}: {e}")
            return False
    
    def get_keys_pattern(self, pattern: str) -> List[str]:
        """Obtener claves que coincidan con un patrón"""
        try:
            conn = self._get_read_connection()
            return conn.keys(pattern)
        except Exception as e:
            logger.error(f"Error obteniendo claves con patrón {pattern}: {e}")
            return []
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Incrementar un contador"""
        try:
            return self.master.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementando {key}: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Obtener estadísticas de Redis"""
        stats = {
            'master': {'status': 'disconnected', 'info': {}},
            'slaves': []
        }
        
        try:
            if self.master:
                info = self.master.info()
                stats['master'] = {
                    'status': 'connected',
                    'host': Config.REDIS_MASTER_HOST,
                    'port': Config.REDIS_MASTER_PORT,
                    'info': {
                        'connected_clients': info.get('connected_clients', 0),
                        'used_memory_human': info.get('used_memory_human', '0'),
                        'keyspace_hits': info.get('keyspace_hits', 0),
                        'keyspace_misses': info.get('keyspace_misses', 0)
                    }
                }
        except Exception as e:
            logger.error(f"Error obteniendo stats del master: {e}")
        
        for i, slave in enumerate(self.slaves):
            try:
                if slave != self.master:  # No duplicar stats del master
                    info = slave.info()
                    host = Config.REDIS_SLAVE1_HOST if i == 0 else Config.REDIS_SLAVE2_HOST
                    port = Config.REDIS_SLAVE1_PORT if i == 0 else Config.REDIS_SLAVE2_PORT
                    stats['slaves'].append({
                        'status': 'connected',
                        'host': host,
                        'port': port,
                        'info': {
                            'connected_clients': info.get('connected_clients', 0),
                            'used_memory_human': info.get('used_memory_human', '0'),
                            'keyspace_hits': info.get('keyspace_hits', 0),
                            'keyspace_misses': info.get('keyspace_misses', 0)
                        }
                    })
            except Exception as e:
                logger.error(f"Error obteniendo stats del slave {i}: {e}")
                stats['slaves'].append({'status': 'disconnected'})
        
        return stats

# Instancia global del caché
cache = RedisCache()