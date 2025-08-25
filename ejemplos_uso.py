#!/usr/bin/env python3
"""
Ejemplos de uso de la API Biblioteca Mejorada
Ejecuta este script para probar todas las funcionalidades
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://127.0.0.1:8000"

def print_response(response, title):
    """Imprime la respuesta de forma legible"""
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print(f"{'='*50}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")
    print(f"{'='*50}")

def test_api():
    """Prueba todas las funcionalidades de la API"""
    
    print("🚀 Iniciando pruebas de la API Biblioteca Mejorada")
    
    # 1. Información de la API
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Información de la API")
    
    # 2. Crear libros de ejemplo
    libros_ejemplo = [
        {
            "titulo": "El Señor de los Anillos",
            "autor": "J.R.R. Tolkien",
            "año": 1954,
            "genero": "Fantasía",
            "isbn": "9788445071405",
            "descripcion": "Una épica historia de fantasía sobre la lucha contra el mal"
        },
        {
            "titulo": "1984",
            "autor": "George Orwell",
            "año": 1949,
            "genero": "Ciencia Ficción",
            "isbn": "9788497594257",
            "descripcion": "Distopía sobre una sociedad totalitaria"
        },
        {
            "titulo": "Cien años de soledad",
            "autor": "Gabriel García Márquez",
            "año": 1967,
            "genero": "Realismo Mágico",
            "isbn": "9788497592208",
            "descripcion": "Obra maestra del realismo mágico latinoamericano"
        },
        {
            "titulo": "El Hobbit",
            "autor": "J.R.R. Tolkien",
            "año": 1937,
            "genero": "Fantasía",
            "isbn": "9788445071406",
            "descripcion": "Aventura de un hobbit en busca de un tesoro"
        },
        {
            "titulo": "Dune",
            "autor": "Frank Herbert",
            "año": 1965,
            "genero": "Ciencia Ficción",
            "isbn": "9788497594258",
            "descripcion": "Épica de ciencia ficción en el desierto de Arrakis"
        }
    ]
    
    libros_creados = []
    for i, libro in enumerate(libros_ejemplo, 1):
        response = requests.post(f"{BASE_URL}/libros/", json=libro)
        print_response(response, f"Creando libro {i}: {libro['titulo']}")
        if response.status_code == 200:
            libros_creados.append(response.json())
    
    # 3. Obtener todos los libros con paginación
    response = requests.get(f"{BASE_URL}/libros/?pagina=1&por_pagina=5")
    print_response(response, "Libros con paginación (5 por página)")
    
    # 4. Obtener libros con filtros
    response = requests.get(f"{BASE_URL}/libros/?genero=Fantasía&ordenar_por=titulo&orden=asc")
    print_response(response, "Libros de Fantasía ordenados por título")
    
    # 5. Búsqueda por autor
    response = requests.get(f"{BASE_URL}/libros/buscar/?q=tolkien&campo=autor")
    print_response(response, "Búsqueda de libros por autor 'tolkien'")
    
    # 6. Búsqueda por título
    response = requests.get(f"{BASE_URL}/libros/buscar/?q=señor&campo=titulo")
    print_response(response, "Búsqueda de libros con 'señor' en el título")
    
    # 7. Obtener estadísticas
    response = requests.get(f"{BASE_URL}/libros/estadisticas/")
    print_response(response, "Estadísticas de la biblioteca")
    
    # 8. Obtener géneros únicos
    response = requests.get(f"{BASE_URL}/libros/generos/")
    print_response(response, "Géneros únicos disponibles")
    
    # 9. Obtener autores únicos
    response = requests.get(f"{BASE_URL}/libros/autores/")
    print_response(response, "Autores únicos disponibles")
    
    # 10. Actualizar un libro (si se creó al menos uno)
    if libros_creados:
        libro_id = libros_creados[0]['id']
        actualizacion = {
            "descripcion": "Descripción actualizada con más detalles sobre la trama"
        }
        response = requests.patch(f"{BASE_URL}/libros/{libro_id}", json=actualizacion)
        print_response(response, f"Actualizando libro ID {libro_id}")
        
        # Ver el libro actualizado
        response = requests.get(f"{BASE_URL}/libros/{libro_id}")
        print_response(response, f"Libro actualizado ID {libro_id}")
    
    # 11. Filtrar por rango de años
    response = requests.get(f"{BASE_URL}/libros/?año_min=1950&año_max=1970&ordenar_por=año&orden=desc")
    print_response(response, "Libros publicados entre 1950 y 1970")
    
    # 12. Obtener libros ordenados por año descendente
    response = requests.get(f"{BASE_URL}/libros/?ordenar_por=año&orden=desc&por_pagina=3")
    print_response(response, "Libros más recientes (ordenados por año descendente)")
    
    print("\n✅ Todas las pruebas completadas!")
    print(f"📖 Visita http://127.0.0.1:8000/docs para ver la documentación interactiva")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        print("💡 Asegúrate de que la API esté ejecutándose en http://127.0.0.1:8000")
        print("   Ejecuta: python main.py")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
