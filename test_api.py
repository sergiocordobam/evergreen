#!/usr/bin/env python3
"""
Script de prueba para el Sistema de Análisis de Producción
Este script demuestra cómo usar la API generada con datos de ejemplo
"""

import requests
import json
from datetime import datetime

# URL base de la API (ajustar si es necesario)
BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Iniciando pruebas del Sistema de Análisis de Producción")
    print("=" * 60)
    
    # 1. Obtener catálogo de productores
    print("\n📋 1. Obteniendo catálogo de productores...")
    try:
        response = requests.get(f"{BASE_URL}/catalogo/productores")
        if response.status_code == 200:
            productores = response.json()
            print(f"✅ Encontrados {len(productores)} productores")
            for p in productores:
                print(f"   - {p['nombre']} (ID: {p['id']}, Área: {p['area']})")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. Asegúrate de que la API esté ejecutándose.")
        return
    
    # 2. Obtener catálogo de productos
    print("\n📋 2. Obteniendo catálogo de productos...")
    try:
        response = requests.get(f"{BASE_URL}/catalogo/productos")
        if response.status_code == 200:
            productos = response.json()
            print(f"✅ Encontrados {len(productos)} productos")
            for p in productos:
                print(f"   - {p['nombre']} (ID: {p['id']})")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        return
    
    # 3. Generar reporte consolidado
    print("\n📊 3. Generando reporte consolidado...")
    try:
        response = requests.get(f"{BASE_URL}/reporte/consolidado")
        if response.status_code == 200:
            print("✅ Reporte consolidado generado exitosamente")
            print("   (Archivo Excel descargado)")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
    
    # 4. Ejemplo de gráfica histórica (asumiendo productor ID 1)
    print("\n📈 4. Generando gráfica histórica para productor ID 1...")
    try:
        response = requests.get(f"{BASE_URL}/grafica/historico/1")
        if response.status_code == 200:
            data = response.json()
            print("✅ Gráfica histórica generada exitosamente")
            print(f"   Total cantidad: {data['resumen']['total_cantidad']}")
            print(f"   Total costos: {data['resumen']['total_costos']}")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
    
    # 5. Top productores (asumiendo producto ID 1, cantidad mínima 50)
    print("\n🏆 5. Obteniendo top productores para producto ID 1...")
    try:
        response = requests.get(f"{BASE_URL}/reporte/top-productores?producto_id=1&cantidad_minima=50")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Encontrados {data['total_productores']} productores")
            for p in data['productores']:
                print(f"   - {p['Productor']}: {p['Total_Cantidad']} unidades")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
    
    # 6. Resumen de costos (asumiendo productor ID 1)
    print("\n💰 6. Obteniendo resumen de costos para productor ID 1...")
    try:
        response = requests.get(f"{BASE_URL}/reporte/resumen-costos/1")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total costos general: {data['total_costos_general']}")
            print(f"   Número de productos: {data['num_productos']}")
            for p in data['resumen_por_producto']:
                print(f"   - {p['Producto']}: {p['Total_Costos']} costos")
        else:
            print(f"❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("\n💡 Para ejecutar la API:")
    print("   uvicorn main:app --reload")
    print("\n📚 Documentación interactiva:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    test_api()
