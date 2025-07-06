import os

class Config:   
    # PostgreSQL config
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '123456')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5433')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'ecommerce')
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis config
    REDIS_MASTER_HOST = os.getenv('REDIS_MASTER_HOST', 'localhost')
    REDIS_MASTER_PORT = int(os.getenv('REDIS_MASTER_PORT', '6379'))
    REDIS_SLAVE1_HOST = os.getenv('REDIS_SLAVE1_HOST', 'localhost')
    REDIS_SLAVE1_PORT = int(os.getenv('REDIS_SLAVE1_PORT', '6380'))
    REDIS_SLAVE2_HOST = os.getenv('REDIS_SLAVE2_HOST', 'localhost')
    REDIS_SLAVE2_PORT = int(os.getenv('REDIS_SLAVE2_PORT', '6381'))
    
    # Cache settings - 30 minutos como requiere el laboratorio
    CACHE_EXPIRATION = 30 * 60  # 30 minutos en segundos