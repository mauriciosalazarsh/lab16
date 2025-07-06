# Carrito de Compras - Patrón Cache-Aside

Sistema de carrito de compras que integra Redis como sistema de caché y PostgreSQL como base de datos persistente, utilizando el patrón Cache-Aside para mejorar el rendimiento y escalabilidad.

## Setup

* pip install -r requirements.txt
* docker-compose up -d
* docker exec -it postgres-ecommerce psql -U postgres -c "CREATE DATABASE ecommerce;"
* python -m scripts.seed_data
* python run.py  
  Aplicación disponible en: http://localhost:5001

## Scripts disponibles

* scripts/cache_aside_verification.py - Verifica la implementación del patrón Cache-Aside.
* scripts/performance_test.py - Ejecuta pruebas de rendimiento.
* scripts/generate_redis_evidence.py - Genera evidencias del uso de Redis (GETs, TTL, consistencia).

## Verificación del funcionamiento

* python scripts/cache_aside_verification.py
* python scripts/performance_test.py
* python scripts/generate_redis_evidence.py

## Endpoints destacados

| Método | Endpoint                | Descripción                                           |
|--------|-------------------------|-------------------------------------------------------|
| GET    | /cart/{user_id}         | Obtiene el carrito del usuario desde Redis o DB      |
| POST   | /cart/{user_id}/add     | Agrega un producto al carrito                        |
| DELETE | /cart/{user_id}/clear   | Vacía el carrito del usuario                         |
| GET    | /stats/top-products     | Muestra los 10 productos más comprados (con caché)   |

## Estructura del Proyecto

text
ecommerce_todo/
├── app/
│   ├── cart.py
│   ├── cart_service.py
│   ├── cart_routes.py
│   ├── redis_cache.py
│   ├── database.py
│   └── config.py
├── scripts/
│   ├── seed_data.py
│   ├── cache_aside_verification.py
│   ├── performance_test.py
│   └── generate_redis_evidence.py
├── docker-compose.yml
├── requirements.txt
└── run.py
