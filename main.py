from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from typing import List, Optional
import os

# Configuración de la base de datos
DATABASE_CONFIG = {
    "host": "caboose.proxy.rlwy.net",
    "port": 50507,
    "user": "root",
    "password": "izCJRQOymGaJYuMmrYTPemjmmczMmRiL",
    "database": "railway"
}

app = FastAPI(title="API Biblioteca Simple", version="1.0.0")

# Modelo Pydantic para Libro
class Libro(BaseModel):
    titulo: str
    autor: str
    año: int
    genero: Optional[str] = None

class LibroResponse(Libro):
    id: int

# Función para conectar a la base de datos
def get_connection():
    try:
        return mysql.connector.connect(**DATABASE_CONFIG)
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {e}")

# Crear tabla si no existe
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(200) NOT NULL,
            autor VARCHAR(100) NOT NULL,
            año INT NOT NULL,
            genero VARCHAR(50)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Inicializar la tabla al arrancar
@app.on_event("startup")
def startup():
    create_table()

# Endpoints CRUD

@app.get("/")
def root():
    return {"mensaje": "API de Biblioteca - FastAPI con MySQL"}

# CREATE - Crear libro
@app.post("/libros/", response_model=LibroResponse)
def crear_libro(libro: Libro):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "INSERT INTO libros (titulo, autor, año, genero) VALUES (%s, %s, %s, %s)"
    values = (libro.titulo, libro.autor, libro.año, libro.genero)
    
    cursor.execute(query, values)
    conn.commit()
    
    libro_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return LibroResponse(id=libro_id, **libro.dict())

# READ - Obtener todos los libros
@app.get("/libros/", response_model=List[LibroResponse])
def obtener_libros():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM libros")
    libros = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return libros

# READ - Obtener libro por ID
@app.get("/libros/{libro_id}", response_model=LibroResponse)
def obtener_libro(libro_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    return libro

# UPDATE - Actualizar libro
@app.put("/libros/{libro_id}", response_model=LibroResponse)
def actualizar_libro(libro_id: int, libro: Libro):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT id FROM libros WHERE id = %s", (libro_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Actualizar
    query = "UPDATE libros SET titulo=%s, autor=%s, año=%s, genero=%s WHERE id=%s"
    values = (libro.titulo, libro.autor, libro.año, libro.genero, libro_id)
    
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    
    return LibroResponse(id=libro_id, **libro.dict())

# DELETE - Eliminar libro
@app.delete("/libros/{libro_id}")
def eliminar_libro(libro_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT id FROM libros WHERE id = %s", (libro_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Eliminar
    cursor.execute("DELETE FROM libros WHERE id = %s", (libro_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"mensaje": "Libro eliminado correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)