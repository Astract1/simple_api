from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import mysql.connector
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_CONFIG = {
    "host": "caboose.proxy.rlwy.net",
    "port": 50507,
    "user": "root",
    "password": "izCJRQOymGaJYuMmrYTPemjmmczMmRiL",
    "database": "railway"
}

app = FastAPI(
    title="API Biblioteca Mejorada", 
    version="2.0.0",
    description="API completa para gestión de biblioteca con búsqueda, filtros y estadísticas"
)

# Modelos Pydantic mejorados
class Libro(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200, description="Título del libro")
    autor: str = Field(..., min_length=1, max_length=100, description="Autor del libro")
    año: int = Field(..., ge=1000, le=datetime.now().year, description="Año de publicación")
    genero: Optional[str] = Field(None, max_length=50, description="Género literario")
    isbn: Optional[str] = Field(None, max_length=13, description="ISBN del libro")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del libro")
    
    @validator('año')
    def validar_año(cls, v):
        if v < 1000 or v > datetime.now().year:
            raise ValueError(f'El año debe estar entre 1000 y {datetime.now().year}')
        return v

class LibroResponse(Libro):
    id: int
    fecha_creacion: Optional[str] = None

class LibroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    autor: Optional[str] = Field(None, min_length=1, max_length=100)
    año: Optional[int] = Field(None, ge=1000, le=datetime.now().year)
    genero: Optional[str] = Field(None, max_length=50)
    isbn: Optional[str] = Field(None, max_length=13)
    descripcion: Optional[str] = Field(None, max_length=500)

class PaginatedResponse(BaseModel):
    libros: List[LibroResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class Estadisticas(BaseModel):
    total_libros: int
    libros_por_genero: dict
    libros_por_año: dict
    autores_unicos: int
    generos_unicos: int

# Función para conectar a la base de datos
def get_connection():
    try:
        return mysql.connector.connect(**DATABASE_CONFIG)
    except mysql.connector.Error as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error de conexión: {e}")

# Crear tabla mejorada si no existe
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear tabla con todos los campos desde el inicio
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(200) NOT NULL,
            autor VARCHAR(100) NOT NULL,
            año INT NOT NULL,
            genero VARCHAR(50),
            isbn VARCHAR(13),
            descripcion TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_titulo (titulo),
            INDEX idx_autor (autor),
            INDEX idx_genero (genero),
            INDEX idx_año (año)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Si la tabla ya existía, intentar agregar las columnas faltantes
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar y agregar columna isbn
        cursor.execute("SHOW COLUMNS FROM libros LIKE 'isbn'")
        if not cursor.fetchall():
            cursor.execute("ALTER TABLE libros ADD COLUMN isbn VARCHAR(13)")
            logger.info("Columna 'isbn' agregada")
        
        # Verificar y agregar columna descripcion
        cursor.execute("SHOW COLUMNS FROM libros LIKE 'descripcion'")
        if not cursor.fetchall():
            cursor.execute("ALTER TABLE libros ADD COLUMN descripcion TEXT")
            logger.info("Columna 'descripcion' agregada")
        
        # Verificar y agregar columna fecha_creacion
        cursor.execute("SHOW COLUMNS FROM libros LIKE 'fecha_creacion'")
        if not cursor.fetchall():
            cursor.execute("ALTER TABLE libros ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            logger.info("Columna 'fecha_creacion' agregada")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"No se pudieron agregar columnas adicionales: {e}")
        try:
            cursor.close()
            conn.close()
        except:
            pass

# Inicializar la tabla al arrancar
@app.on_event("startup")
def startup():
    create_table()
    logger.info("API iniciada y tabla creada/verificada")

# Endpoints mejorados

@app.get("/", tags=["Información"])
def root():
    return {
        "mensaje": "API de Biblioteca Mejorada - FastAPI con MySQL",
        "version": "2.0.0",
        "endpoints": {
            "libros": "/libros/",
            "buscar": "/libros/buscar/",
            "estadisticas": "/libros/estadisticas/",
            "documentacion": "/docs"
        }
    }

# CREATE - Crear libro
@app.post("/libros/", response_model=LibroResponse, tags=["CRUD"])
def crear_libro(libro: Libro):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO libros (titulo, autor, año, genero, isbn, descripcion) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (libro.titulo, libro.autor, libro.año, libro.genero, libro.isbn, libro.descripcion)
    
    try:
        cursor.execute(query, values)
        conn.commit()
        libro_id = cursor.lastrowid
        
        # Obtener el libro creado
        cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
        libro_creado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Libro creado: {libro.titulo} por {libro.autor}")
        
        return LibroResponse(
            id=libro_creado[0],
            titulo=libro_creado[1],
            autor=libro_creado[2],
            año=libro_creado[3],
            genero=libro_creado[4],
            isbn=libro_creado[5],
            descripcion=libro_creado[6],
            fecha_creacion=str(libro_creado[7])
        )
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al crear libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear libro: {e}")

# READ - Obtener libros con paginación y filtros
@app.get("/libros/", response_model=PaginatedResponse, tags=["CRUD"])
def obtener_libros(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Libros por página"),
    ordenar_por: str = Query("id", description="Campo para ordenar (id, titulo, autor, año, genero)"),
    orden: str = Query("asc", description="Orden (asc o desc)"),
    genero: Optional[str] = Query(None, description="Filtrar por género"),
    año_min: Optional[int] = Query(None, ge=1000, description="Año mínimo"),
    año_max: Optional[int] = Query(None, le=datetime.now().year, description="Año máximo")
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Construir query base
    query = "SELECT * FROM libros WHERE 1=1"
    params = []
    
    # Aplicar filtros
    if genero:
        query += " AND genero = %s"
        params.append(genero)
    
    if año_min:
        query += " AND año >= %s"
        params.append(año_min)
    
    if año_max:
        query += " AND año <= %s"
        params.append(año_max)
    
    # Contar total
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total = cursor.fetchone()['COUNT(*)']
    
    # Aplicar ordenamiento
    campos_validos = ['id', 'titulo', 'autor', 'año', 'genero']
    if ordenar_por not in campos_validos:
        ordenar_por = 'id'
    
    orden = 'ASC' if orden.lower() == 'asc' else 'DESC'
    query += f" ORDER BY {ordenar_por} {orden}"
    
    # Aplicar paginación
    offset = (pagina - 1) * por_pagina
    query += " LIMIT %s OFFSET %s"
    params.extend([por_pagina, offset])
    
    cursor.execute(query, params)
    libros_raw = cursor.fetchall()
    
    # Convertir datetime a string
    libros = []
    for libro in libros_raw:
        libro_dict = dict(libro)
        if libro_dict.get('fecha_creacion'):
            libro_dict['fecha_creacion'] = str(libro_dict['fecha_creacion'])
        libros.append(libro_dict)
    
    cursor.close()
    conn.close()
    
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return PaginatedResponse(
        libros=libros,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas
    )

# BÚSQUEDA AVANZADA
@app.get("/libros/buscar/", response_model=List[LibroResponse], tags=["Búsqueda"])
def buscar_libros(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    campo: str = Query("titulo", description="Campo a buscar (titulo, autor, genero, descripcion)")
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    campos_validos = ['titulo', 'autor', 'genero', 'descripcion']
    if campo not in campos_validos:
        campo = 'titulo'
    
    query = f"SELECT * FROM libros WHERE {campo} LIKE %s ORDER BY titulo"
    search_term = f"%{q}%"
    
    cursor.execute(query, (search_term,))
    libros_raw = cursor.fetchall()
    
    # Convertir datetime a string
    libros = []
    for libro in libros_raw:
        libro_dict = dict(libro)
        if libro_dict.get('fecha_creacion'):
            libro_dict['fecha_creacion'] = str(libro_dict['fecha_creacion'])
        libros.append(libro_dict)
    
    cursor.close()
    conn.close()
    
    logger.info(f"Búsqueda realizada: '{q}' en campo '{campo}', {len(libros)} resultados")
    return libros

# READ - Obtener libro por ID
@app.get("/libros/{libro_id}", response_model=LibroResponse, tags=["CRUD"])
def obtener_libro(libro_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Convertir datetime a string
    if libro.get('fecha_creacion'):
        libro['fecha_creacion'] = str(libro['fecha_creacion'])
    
    return libro

# UPDATE - Actualizar libro (parcial)
@app.patch("/libros/{libro_id}", response_model=LibroResponse, tags=["CRUD"])
def actualizar_libro(libro_id: int, libro_update: LibroUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT id FROM libros WHERE id = %s", (libro_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Construir query de actualización dinámica
    update_fields = []
    values = []
    
    for field, value in libro_update.dict(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = %s")
            values.append(value)
    
    if not update_fields:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    values.append(libro_id)
    query = f"UPDATE libros SET {', '.join(update_fields)} WHERE id = %s"
    
    cursor.execute(query, values)
    conn.commit()
    
    # Obtener libro actualizado
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro_actualizado = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    logger.info(f"Libro {libro_id} actualizado")
    
    return LibroResponse(
        id=libro_actualizado[0],
        titulo=libro_actualizado[1],
        autor=libro_actualizado[2],
        año=libro_actualizado[3],
        genero=libro_actualizado[4],
        isbn=libro_actualizado[5],
        descripcion=libro_actualizado[6],
        fecha_creacion=str(libro_actualizado[7])
    )

# DELETE - Eliminar libro
@app.delete("/libros/{libro_id}", tags=["CRUD"])
def eliminar_libro(libro_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT titulo FROM libros WHERE id = %s", (libro_id,))
    libro = cursor.fetchone()
    if not libro:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Eliminar
    cursor.execute("DELETE FROM libros WHERE id = %s", (libro_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Libro eliminado: {libro[0]} (ID: {libro_id})")
    return {"mensaje": f"Libro '{libro[0]}' eliminado correctamente"}

# ESTADÍSTICAS
@app.get("/libros/estadisticas/", response_model=Estadisticas, tags=["Estadísticas"])
def obtener_estadisticas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Total de libros
    cursor.execute("SELECT COUNT(*) as total FROM libros")
    total_libros = cursor.fetchone()['total']
    
    # Libros por género
    cursor.execute("""
        SELECT genero, COUNT(*) as cantidad 
        FROM libros 
        WHERE genero IS NOT NULL 
        GROUP BY genero 
        ORDER BY cantidad DESC
    """)
    libros_por_genero = {row['genero']: row['cantidad'] for row in cursor.fetchall()}
    
    # Libros por año (últimos 10 años)
    cursor.execute("""
        SELECT año, COUNT(*) as cantidad 
        FROM libros 
        WHERE año >= YEAR(NOW()) - 10
        GROUP BY año 
        ORDER BY año DESC
    """)
    libros_por_año = {str(row['año']): row['cantidad'] for row in cursor.fetchall()}
    
    # Autores únicos
    cursor.execute("SELECT COUNT(DISTINCT autor) as autores FROM libros")
    autores_unicos = cursor.fetchone()['autores']
    
    # Géneros únicos
    cursor.execute("SELECT COUNT(DISTINCT genero) as generos FROM libros WHERE genero IS NOT NULL")
    generos_unicos = cursor.fetchone()['generos']
    
    cursor.close()
    conn.close()
    
    return Estadisticas(
        total_libros=total_libros,
        libros_por_genero=libros_por_genero,
        libros_por_año=libros_por_año,
        autores_unicos=autores_unicos,
        generos_unicos=generos_unicos
    )

# ENDPOINT PARA OBTENER GÉNEROS ÚNICOS
@app.get("/libros/generos/", tags=["Utilidades"])
def obtener_generos():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT genero FROM libros WHERE genero IS NOT NULL ORDER BY genero")
    generos = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return {"generos": generos}

# ENDPOINT PARA OBTENER AUTORES ÚNICOS
@app.get("/libros/autores/", tags=["Utilidades"])
def obtener_autores():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT autor FROM libros ORDER BY autor")
    autores = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return {"autores": autores}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)