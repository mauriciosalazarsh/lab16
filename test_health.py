#!/usr/bin/env python3
"""
Script para debuggear el health check
"""

import requests

def test_health_endpoints():
    base_url = "http://localhost:5001"
    
    print("Probando endpoints de health...")
    
    # Test 1: Health general
    try:
        response = requests.get(f"{base_url}/health")
        print(f"GET /health: {response.status_code}")
        if response.status_code == 200:
            print(f"  Respuesta: {response.json()}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"GET /health: ERROR - {e}")
    
    # Test 2: Cart health
    try:
        response = requests.get(f"{base_url}/cart/health")
        print(f"GET /cart/health: {response.status_code}")
        if response.status_code == 200:
            print(f"  Respuesta: {response.json()}")
    except Exception as e:
        print(f"GET /cart/health: ERROR - {e}")
    
    # Test 3: Root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"GET /: {response.status_code}")
        if response.status_code == 200:
            print(f"  Respuesta: {response.json()}")
    except Exception as e:
        print(f"GET /: ERROR - {e}")

if __name__ == '__main__':
    test_health_endpoints()