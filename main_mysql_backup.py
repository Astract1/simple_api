from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime, date, timedelta
import logging
import random
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de MongoDB
MONGODB_URL = "mongodb+srv://diegojimenez2432_db_user:ZVgDJ4EYuti4LLQE@clusterjuan.mx2coel.mongodb.net/"
DATABASE_NAME = "biblioteca_db"

# Cliente MongoDB
client = None
db = None

# Función para conectar a MongoDB
async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        # Verificar conexión
        await client.admin.command('ping')
        logger.info("✅ Conectado exitosamente a MongoDB")
    except Exception as e:
        logger.error(f"Error de conexión a MongoDB: {e}")
        raise HTTPException(status_code=500, detail=f"Error de conexión: {e}")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("🔌 Desconectado de MongoDB")

# Modelos Pydantic - LIBROS
class Libro(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200, description="Título del libro")
    autor: str = Field(..., min_length=1, max_length=100, description="Autor del libro")
    año: int = Field(..., ge=1000, le=datetime.now().year, description="Año de publicación")
    genero: Optional[str] = Field(None, max_length=50, description="Género literario")
    isbn: Optional[str] = Field(None, max_length=13, description="ISBN del libro")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del libro")
    
    @field_validator('año')
    @classmethod
    def validar_año(cls, v):
        if v < 1000 or v > datetime.now().year:
            raise ValueError(f'El año debe estar entre 1000 y {datetime.now().year}')
        return v

class LibroResponse(Libro):
    id: str = Field(alias="_id")
    fecha_creacion: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class LibroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    autor: Optional[str] = Field(None, min_length=1, max_length=100)
    año: Optional[int] = Field(None, ge=1000, le=datetime.now().year)
    genero: Optional[str] = Field(None, max_length=50)
    isbn: Optional[str] = Field(None, max_length=13)
    descripcion: Optional[str] = Field(None, max_length=500)

# Modelos Pydantic - USUARIOS
class Usuario(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo")
    email: str = Field(..., max_length=150, description="Correo electrónico")
    telefono: Optional[str] = Field(None, max_length=15, description="Número de teléfono")
    direccion: Optional[str] = Field(None, max_length=300, description="Dirección")
    tipo_usuario: str = Field("estudiante", description="Tipo de usuario (estudiante, profesor, administrador)")

class UsuarioResponse(Usuario):
    id: str = Field(alias="_id")
    fecha_registro: Optional[str] = None
    activo: bool = True
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=15)
    direccion: Optional[str] = Field(None, max_length=300)
    tipo_usuario: Optional[str] = None
    activo: Optional[bool] = None

# Modelos Pydantic - PRÉSTAMOS
class Prestamo(BaseModel):
    libro_id: str = Field(..., description="ID del libro a prestar")
    usuario_id: str = Field(..., description="ID del usuario")
    fecha_devolucion_esperada: str = Field(..., description="Fecha esperada de devolución (YYYY-MM-DD)")

class PrestamoResponse(BaseModel):
    id: str = Field(alias="_id")
    libro_id: str
    usuario_id: str
    fecha_prestamo: str
    fecha_devolucion_esperada: str
    fecha_devolucion_real: Optional[str] = None
    estado: str
    libro_titulo: Optional[str] = None
    usuario_nombre: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class PrestamoUpdate(BaseModel):
    fecha_devolucion_esperada: Optional[str] = None
    estado: Optional[str] = None

# Modelos Pydantic - RESEÑAS
class Reseña(BaseModel):
    libro_id: str = Field(..., description="ID del libro a reseñar")
    usuario_id: str = Field(..., description="ID del usuario que hace la reseña")
    calificacion: int = Field(..., ge=1, le=5, description="Calificación del 1 al 5")
    comentario: Optional[str] = Field(None, max_length=1000, description="Comentario sobre el libro")

class ReseñaResponse(Reseña):
    id: str = Field(alias="_id")
    fecha_reseña: str
    libro_titulo: Optional[str] = None
    usuario_nombre: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ReseñaUpdate(BaseModel):
    calificacion: Optional[int] = Field(None, ge=1, le=5)
    comentario: Optional[str] = Field(None, max_length=1000)

# Modelos de respuesta paginada
class PaginatedResponse(BaseModel):
    libros: List[LibroResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class PaginatedUsuariosResponse(BaseModel):
    usuarios: List[UsuarioResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class PaginatedPrestamosResponse(BaseModel):
    prestamos: List[PrestamoResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class PaginatedReseñasResponse(BaseModel):
    reseñas: List[ReseñaResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class Estadisticas(BaseModel):
    total_libros: int
    total_usuarios: int
    total_prestamos: int
    total_reseñas: int
    libros_por_genero: dict
    libros_por_año: dict
    usuarios_por_tipo: dict
    prestamos_activos: int
    prestamos_vencidos: int
    promedio_calificaciones: float
    autores_unicos: int
    generos_unicos: int

# Crear índices en las colecciones de MongoDB
async def create_indexes():
    try:
        # Índices para la colección libros
        await db.libros.create_index([("titulo", 1)])
        await db.libros.create_index([("autor", 1)])
        await db.libros.create_index([("genero", 1)])
        await db.libros.create_index([("año", 1)])
        
        # Índices para la colección usuarios
        await db.usuarios.create_index([("email", 1)], unique=True)
        await db.usuarios.create_index([("tipo_usuario", 1)])
        await db.usuarios.create_index([("activo", 1)])
        
        # Índices para la colección prestamos
        await db.prestamos.create_index([("libro_id", 1)])
        await db.prestamos.create_index([("usuario_id", 1)])
        await db.prestamos.create_index([("estado", 1)])
        await db.prestamos.create_index([("fecha_devolucion_esperada", 1)])
        
        # Índices para la colección reseñas
        await db.reseñas.create_index([("libro_id", 1)])
        await db.reseñas.create_index([("usuario_id", 1)])
        await db.reseñas.create_index([("calificacion", 1)])
        await db.reseñas.create_index([("libro_id", 1), ("usuario_id", 1)], unique=True)
        
        logger.info("✅ Índices creados exitosamente en MongoDB")
    except Exception as e:
        logger.error(f"Error al crear índices: {e}")

# Función para poblar MongoDB con datos de prueba
async def poblar_datos_iniciales():
    try:
        # Verificar si ya hay datos
        libros_count = await db.libros.count_documents({})
        if libros_count > 0:
            logger.info("La base de datos ya contiene datos, omitiendo población inicial")
            return
        
        logger.info("Poblando base de datos con datos iniciales...")
        
        # DATOS REALISTAS PARA LIBROS
        libros_data = [
            ("Cien años de soledad", "Gabriel García Márquez", 1967, "Realismo mágico", "9780307474728", 
             "La épica historia de la familia Buendía a lo largo de siete generaciones en el pueblo ficticio de Macondo."),
            ("1984", "George Orwell", 1949, "Distopía", "9780451524935",
             "Una novela distópica que presenta un mundo totalitario donde el gobierno controla todos los aspectos de la vida."),
            ("El principito", "Antoine de Saint-Exupéry", 1943, "Fábula", "9780156012195",
             "Una fábula poética sobre un pequeño príncipe que viaja por diferentes planetas."),
            ("Don Quijote de la Mancha", "Miguel de Cervantes", 1605, "Clásico", "9788420412146",
             "Las aventuras del ingenioso hidalgo Don Quijote y su fiel escudero Sancho Panza."),
            ("Rayuela", "Julio Cortázar", 1963, "Literatura experimental", "9788437604572",
             "Una novela experimental que puede leerse de múltiples maneras, siguiendo diferentes secuencias."),
            ("La casa de los espíritus", "Isabel Allende", 1982, "Realismo mágico", "9780553383805",
             "La saga de la familia del Valle a través de cuatro generaciones de mujeres."),
            ("Beloved", "Toni Morrison", 1987, "Drama histórico", "9781400033416",
             "Una poderosa novela sobre la esclavitud y sus consecuencias en Estados Unidos."),
            ("El amor en los tiempos del cólera", "Gabriel García Márquez", 1985, "Romance", "9780307389732",
             "Una historia de amor que perdura más de cincuenta años entre Florentino Ariza y Fermina Daza."),
            ("Midnight's Children", "Salman Rushdie", 1981, "Realismo mágico", "9780812976533",
             "La historia de Saleem Sinai, nacido en el momento de la independencia de la India."),
            ("La metamorfosis", "Franz Kafka", 1915, "Surrealismo", "9780486290300",
             "La extraña transformación de Gregor Samsa en un insecto gigantesco."),
            ("Orgullo y prejuicio", "Jane Austen", 1813, "Romance clásico", "9780141439518",
             "La historia de Elizabeth Bennet y su compleja relación con el orgulloso Sr. Darcy."),
            ("Fahrenheit 451", "Ray Bradbury", 1953, "Ciencia ficción", "9781451673319",
             "Una sociedad futura donde los libros están prohibidos y los bomberos los queman."),
            ("El gran Gatsby", "F. Scott Fitzgerald", 1925, "Drama", "9780743273565",
             "La historia del misterioso millonario Jay Gatsby y su obsesión por Daisy Buchanan."),
            ("Matar un ruiseñor", "Harper Lee", 1960, "Drama social", "9780060935467",
             "Una historia sobre la injusticia racial en el sur de Estados Unidos vista a través de los ojos de una niña."),
            ("Los pilares de la Tierra", "Ken Follett", 1989, "Ficción histórica", "9780451166890",
             "La construcción de una catedral en la Inglaterra medieval como trasfondo de una épica historia.")
        ]
        
        # Insertar libros en MongoDB
        libros_documentos = []
        for libro in libros_data:
            libro_doc = {
                "titulo": libro[0],
                "autor": libro[1],
                "año": libro[2],
                "genero": libro[3],
                "isbn": libro[4],
                "descripcion": libro[5],
                "fecha_creacion": datetime.now()
            }
            libros_documentos.append(libro_doc)
        
        await db.libros.insert_many(libros_documentos)
        
        # DATOS REALISTAS PARA USUARIOS  
        usuarios_data = [
            ("Ana María González", "ana.gonzalez@email.com", "+34612345678", "Calle Mayor 15, Madrid", "estudiante"),
            ("Carlos Eduardo Martínez", "carlos.martinez@universidad.edu", "+34687654321", "Avenida Libertad 42, Barcelona", "profesor"),
            ("Lucía Fernández Silva", "lucia.fernandez@gmail.com", "+34654321987", "Plaza España 8, Valencia", "estudiante"),
            ("Dr. Roberto Jiménez", "r.jimenez@biblioteca.edu", "+34623456789", "Calle Cervantes 23, Sevilla", "administrador"),
            ("María Elena Torres", "me.torres@email.com", "+34656789012", "Ronda San Pedro 67, Bilbao", "estudiante"),
            ("Prof. Miguel Ángel Ruiz", "ma.ruiz@universidad.edu", "+34634567890", "Calle Goya 34, Zaragoza", "profesor"),
            ("Carmen Delgado Pérez", "carmen.delgado@gmail.com", "+34645678901", "Avenida Constitución 56, Málaga", "estudiante"),
            ("Alejandro Morales", "a.morales@biblioteca.org", "+34612987654", "Calle Velázquez 89, Granada", "administrador"),
            ("Sofía Herrera Castro", "sofia.herrera@email.com", "+34623987654", "Plaza Mayor 12, Salamanca", "estudiante"),
            ("Daniel Ortega López", "daniel.ortega@universidad.edu", "+34654987321", "Calle Picasso 78, Córdoba", "profesor"),
            ("Isabel Ramírez", "isabel.ramirez@gmail.com", "+34665432109", "Avenida Andalucía 45, Cádiz", "estudiante"),
            ("Fernando Castro Gil", "f.castro@email.com", "+34678901234", "Calle Rosalía 67, Santiago", "estudiante"),
            ("Dra. Patricia Vega", "p.vega@universidad.edu", "+34689012345", "Plaza Cataluña 23, Girona", "profesor"),
            ("Javier Mendoza Ruiz", "j.mendoza@biblioteca.org", "+34690123456", "Calle Murillo 56, Toledo", "administrador"),
            ("Natalia Campos", "natalia.campos@email.com", "+34601234567", "Avenida Valencia 89, Alicante", "estudiante")
        ]
        
        # Insertar usuarios en MongoDB
        usuarios_documentos = []
        for usuario in usuarios_data:
            usuario_doc = {
                "nombre": usuario[0],
                "email": usuario[1],
                "telefono": usuario[2],
                "direccion": usuario[3],
                "tipo_usuario": usuario[4],
                "activo": True,
                "fecha_registro": datetime.now()
            }
            usuarios_documentos.append(usuario_doc)
        
        await db.usuarios.insert_many(usuarios_documentos)
        
        # Obtener IDs insertados para crear relaciones
        libros_cursor = db.libros.find({}, {"_id": 1})
        libro_ids = [doc["_id"] async for doc in libros_cursor]
        
        usuarios_cursor = db.usuarios.find({}, {"_id": 1})
        usuario_ids = [doc["_id"] async for doc in usuarios_cursor]
        
        # CREAR PRÉSTAMOS REALISTAS
        prestamos_creados = []
        fecha_actual = date.today()
        
        # Crear 20 préstamos variados
        for _ in range(20):
            libro_id = random.choice(libro_ids)
            usuario_id = random.choice(usuario_ids)
            
            # Evitar duplicados de libro-usuario activos
            if any(p[0] == libro_id and p[1] == usuario_id for p in prestamos_creados if len(p) > 3 and p[3] == 'activo'):
                continue
                
            # Fechas realistas
            dias_atras = random.randint(1, 90)
            fecha_prestamo = fecha_actual - timedelta(days=dias_atras)
            fecha_devolucion_esperada = fecha_prestamo + timedelta(days=random.randint(14, 30))
            
            # Estados realistas
            if fecha_devolucion_esperada < fecha_actual:
                # Préstamo que debería estar vencido
                if random.random() < 0.7:  # 70% se devuelven a tiempo
                    estado = 'devuelto'
                    fecha_devolucion_real = fecha_devolucion_esperada - timedelta(days=random.randint(1, 5))
                else:  # 30% se vencen
                    estado = 'vencido'
                    fecha_devolucion_real = None
            else:
                # Préstamo actual
                if random.random() < 0.2:  # 20% ya devueltos
                    estado = 'devuelto'
                    fecha_devolucion_real = fecha_actual - timedelta(days=random.randint(1, 7))
                else:  # 80% activos
                    estado = 'activo'
                    fecha_devolucion_real = None
            
            prestamo_doc = {
                "libro_id": libro_id,
                "usuario_id": usuario_id,
                "fecha_prestamo": fecha_prestamo,
                "fecha_devolucion_esperada": fecha_devolucion_esperada,
                "fecha_devolucion_real": fecha_devolucion_real,
                "estado": estado
            }
            await db.prestamos.insert_one(prestamo_doc)
            
            prestamos_creados.append((libro_id, usuario_id, fecha_prestamo, estado))
        
        # CREAR RESEÑAS REALISTAS
        comentarios_realistas = [
            "Una obra maestra de la literatura. Totalmente recomendable.",
            "Me encantó la profundidad de los personajes y la narrativa envolvente.",
            "Un clásico que nunca pasa de moda. Excelente lectura.",
            "La historia me mantuvo enganchado desde la primera página.",
            "Interesante perspectiva, aunque un poco lento al principio.",
            "Brillante trabajo del autor. Una lectura obligatoria.",
            "Me gustó mucho, aunque esperaba un final diferente.",
            "Libro fascinante que te hace reflexionar sobre muchas cosas.",
            "No pudo captar mi atención completamente, pero tiene sus momentos.",
            "Una historia emotiva y muy bien escrita. Lo recomiendo.",
            "Excelente desarrollo de la trama. Muy satisfactorio.",
            "Un poco denso para mi gusto, pero reconozco su valor literario.",
            "Me sorprendió gratamente. Una lectura muy enriquecedora.",
            "Historia conmovedora que te llega al corazón.",
            "Buen libro, aunque algunas partes se sienten repetitivas."
        ]
        
        # Crear 25 reseñas
        reseñas_creadas = set()
        for _ in range(25):
            libro_id = random.choice(libro_ids)
            usuario_id = random.choice(usuario_ids)
            
            # Evitar reseñas duplicadas (misma combinación libro-usuario)
            if (libro_id, usuario_id) in reseñas_creadas:
                continue
                
            calificacion = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]  # Más probabilidad de buenas calificaciones
            comentario = random.choice(comentarios_realistas)
            
            # Fecha de reseña realista (después del préstamo si existe)
            fecha_reseña = fecha_actual - timedelta(days=random.randint(1, 60))
            
            reseña_doc = {
                "libro_id": libro_id,
                "usuario_id": usuario_id,
                "calificacion": calificacion,
                "comentario": comentario,
                "fecha_reseña": fecha_reseña
            }
            await db.reseñas.insert_one(reseña_doc)
            
            reseñas_creadas.add((libro_id, usuario_id))
        
        logger.info("✅ Base de datos poblada exitosamente con:")
        logger.info(f"   📚 {len(libros_data)} libros")
        logger.info(f"   👥 {len(usuarios_data)} usuarios") 
        logger.info(f"   📋 20 préstamos")
        logger.info(f"   ⭐ 25 reseñas")
        
    except Exception as e:
        logger.error(f"Error al poblar datos iniciales: {e}")
        raise

# Función de lifespan para inicializar MongoDB
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    await create_indexes()
    await poblar_datos_iniciales()
    logger.info("🚀 API iniciada - MongoDB conectado y datos poblados automáticamente")
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="API Biblioteca Mejorada", 
    version="3.0.0",
    description="Sistema completo de biblioteca con usuarios, préstamos y reseñas",
    lifespan=lifespan
)

# Endpoints principales

@app.get("/", tags=["Información"])
def root():
    return {
        "mensaje": "API de Biblioteca Mejorada - FastAPI con MongoDB",
        "version": "3.0.0",
        "descripcion": "Sistema completo de biblioteca con usuarios, préstamos y reseñas",
        "endpoints": {
            "libros": "/libros/",
            "usuarios": "/usuarios/",
            "prestamos": "/prestamos/",
            "reseñas": "/reseñas/",
            "buscar_libros": "/libros/buscar/",
            "estadisticas_completas": "/estadisticas/",
            "documentacion": "/docs"
        }
    }

# =============================================================================
# ENDPOINTS LIBROS
# =============================================================================

# CREATE - Crear libro
@app.post("/libros/", response_model=LibroResponse, tags=["Libros"])
async def crear_libro(libro: Libro):
    try:
        libro_doc = {
            "titulo": libro.titulo,
            "autor": libro.autor,
            "año": libro.año,
            "genero": libro.genero,
            "isbn": libro.isbn,
            "descripcion": libro.descripcion,
            "fecha_creacion": datetime.now()
        }
        
        result = await db.libros.insert_one(libro_doc)
        libro_creado = await db.libros.find_one({"_id": result.inserted_id})
        
        logger.info(f"Libro creado: {libro.titulo} por {libro.autor}")
        
        return LibroResponse(
            _id=str(libro_creado["_id"]),
            titulo=libro_creado["titulo"],
            autor=libro_creado["autor"],
            año=libro_creado["año"],
            genero=libro_creado["genero"],
            isbn=libro_creado["isbn"],
            descripcion=libro_creado["descripcion"],
            fecha_creacion=str(libro_creado["fecha_creacion"])
        )
    except Exception as e:
        logger.error(f"Error al crear libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear libro: {e}")

# READ - Obtener libros con paginación y filtros
@app.get("/libros/", response_model=PaginatedResponse, tags=["Libros"])
async def obtener_libros(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Libros por página"),
    ordenar_por: str = Query("_id", description="Campo para ordenar (_id, titulo, autor, año, genero)"),
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

# READ - Obtener libro por ID
@app.get("/libros/{libro_id}", response_model=LibroResponse, tags=["Libros"])
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

# UPDATE - Editar libro por ID
@app.put("/libros/{libro_id}", response_model=LibroResponse, tags=["Libros"])
def editar_libro(libro_id: int, libro_actualizado: LibroUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el libro existe
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro_existente = cursor.fetchone()
    if not libro_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Construir query de actualización solo con campos proporcionados
    campos_actualizar = []
    valores = []
    
    if libro_actualizado.titulo is not None:
        campos_actualizar.append("titulo = %s")
        valores.append(libro_actualizado.titulo)
    
    if libro_actualizado.autor is not None:
        campos_actualizar.append("autor = %s")
        valores.append(libro_actualizado.autor)
    
    if libro_actualizado.año is not None:
        campos_actualizar.append("año = %s")
        valores.append(libro_actualizado.año)
    
    if libro_actualizado.genero is not None:
        campos_actualizar.append("genero = %s")
        valores.append(libro_actualizado.genero)
    
    if libro_actualizado.isbn is not None:
        campos_actualizar.append("isbn = %s")
        valores.append(libro_actualizado.isbn)
    
    if libro_actualizado.descripcion is not None:
        campos_actualizar.append("descripcion = %s")
        valores.append(libro_actualizado.descripcion)
    
    # Si no hay campos para actualizar
    if not campos_actualizar:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    # Ejecutar actualización
    valores.append(libro_id)
    query = f"UPDATE libros SET {', '.join(campos_actualizar)} WHERE id = %s"
    
    try:
        cursor.execute(query, valores)
        conn.commit()
        
        # Obtener el libro actualizado
        cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
        libro_actualizado_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Libro actualizado: ID {libro_id}")
        
        return LibroResponse(
            id=libro_actualizado_result[0],
            titulo=libro_actualizado_result[1],
            autor=libro_actualizado_result[2],
            año=libro_actualizado_result[3],
            genero=libro_actualizado_result[4],
            isbn=libro_actualizado_result[5],
            descripcion=libro_actualizado_result[6],
            fecha_creacion=str(libro_actualizado_result[7])
        )
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al actualizar libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar libro: {e}")

# DELETE - Eliminar libro por ID
@app.delete("/libros/{libro_id}", tags=["Libros"])
def eliminar_libro(libro_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el libro existe
    cursor.execute("SELECT titulo, autor FROM libros WHERE id = %s", (libro_id,))
    libro_existente = cursor.fetchone()
    if not libro_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Verificar si el libro tiene préstamos activos
    cursor.execute("""
        SELECT COUNT(*) as activos 
        FROM prestamos 
        WHERE libro_id = %s AND estado = 'activo'
    """, (libro_id,))
    prestamos_activos = cursor.fetchone()[0]
    
    if prestamos_activos > 0:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el libro porque tiene {prestamos_activos} préstamo(s) activo(s)"
        )
    
    try:
        # Eliminar el libro (esto también eliminará automáticamente los préstamos y reseñas asociadas por CASCADE)
        cursor.execute("DELETE FROM libros WHERE id = %s", (libro_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Libro eliminado: '{libro_existente[0]}' por {libro_existente[1]} (ID: {libro_id})")
        
        return {
            "mensaje": "Libro eliminado exitosamente",
            "libro_eliminado": {
                "id": libro_id,
                "titulo": libro_existente[0],
                "autor": libro_existente[1]
            }
        }
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al eliminar libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar libro: {e}")

# =============================================================================
# ENDPOINTS USUARIOS
# =============================================================================

# CREATE - Crear usuario
@app.post("/usuarios/", response_model=UsuarioResponse, tags=["Usuarios"])
def crear_usuario(usuario: Usuario):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO usuarios (nombre, email, telefono, direccion, tipo_usuario) 
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (usuario.nombre, usuario.email, usuario.telefono, usuario.direccion, usuario.tipo_usuario)
    
    try:
        cursor.execute(query, values)
        conn.commit()
        usuario_id = cursor.lastrowid
        
        # Obtener el usuario creado
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        usuario_creado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Usuario creado: {usuario.nombre} ({usuario.email})")
        
        return UsuarioResponse(
            id=usuario_creado[0],
            nombre=usuario_creado[1],
            email=usuario_creado[2],
            telefono=usuario_creado[3],
            direccion=usuario_creado[4],
            tipo_usuario=usuario_creado[5],
            activo=usuario_creado[6],
            fecha_registro=str(usuario_creado[7])
        )
    except mysql.connector.IntegrityError as e:
        cursor.close()
        conn.close()
        logger.error(f"Error de integridad al crear usuario: {e}")
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al crear usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {e}")

# READ - Obtener usuarios con paginación y filtros
@app.get("/usuarios/", response_model=PaginatedUsuariosResponse, tags=["Usuarios"])
def obtener_usuarios(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Usuarios por página"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo de usuario"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo")
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Construir query base
    query = "SELECT * FROM usuarios WHERE 1=1"
    params = []
    
    # Aplicar filtros
    if tipo_usuario:
        query += " AND tipo_usuario = %s"
        params.append(tipo_usuario)
    
    if activo is not None:
        query += " AND activo = %s"
        params.append(activo)
    
    # Contar total
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total = cursor.fetchone()['COUNT(*)']
    
    # Aplicar ordenamiento
    query += " ORDER BY fecha_registro DESC"
    
    # Aplicar paginación
    offset = (pagina - 1) * por_pagina
    query += " LIMIT %s OFFSET %s"
    params.extend([por_pagina, offset])
    
    cursor.execute(query, params)
    usuarios_raw = cursor.fetchall()
    
    # Convertir datetime a string
    usuarios = []
    for usuario in usuarios_raw:
        usuario_dict = dict(usuario)
        if usuario_dict.get('fecha_registro'):
            usuario_dict['fecha_registro'] = str(usuario_dict['fecha_registro'])
        usuarios.append(usuario_dict)
    
    cursor.close()
    conn.close()
    
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return PaginatedUsuariosResponse(
        usuarios=usuarios,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas
    )

# READ - Obtener usuario por ID
@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuarios"])
def obtener_usuario(usuario_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Convertir datetime a string
    if usuario.get('fecha_registro'):
        usuario['fecha_registro'] = str(usuario['fecha_registro'])
    
    return usuario

# UPDATE - Editar usuario por ID
@app.put("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuarios"])
def editar_usuario(usuario_id: int, usuario_actualizado: UsuarioUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el usuario existe
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario_existente = cursor.fetchone()
    if not usuario_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Construir query de actualización solo con campos proporcionados
    campos_actualizar = []
    valores = []
    
    if usuario_actualizado.nombre is not None:
        campos_actualizar.append("nombre = %s")
        valores.append(usuario_actualizado.nombre)
    
    if usuario_actualizado.email is not None:
        campos_actualizar.append("email = %s")
        valores.append(usuario_actualizado.email)
    
    if usuario_actualizado.telefono is not None:
        campos_actualizar.append("telefono = %s")
        valores.append(usuario_actualizado.telefono)
    
    if usuario_actualizado.direccion is not None:
        campos_actualizar.append("direccion = %s")
        valores.append(usuario_actualizado.direccion)
    
    if usuario_actualizado.tipo_usuario is not None:
        campos_actualizar.append("tipo_usuario = %s")
        valores.append(usuario_actualizado.tipo_usuario)
    
    if usuario_actualizado.activo is not None:
        campos_actualizar.append("activo = %s")
        valores.append(usuario_actualizado.activo)
    
    # Si no hay campos para actualizar
    if not campos_actualizar:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    # Ejecutar actualización
    valores.append(usuario_id)
    query = f"UPDATE usuarios SET {', '.join(campos_actualizar)} WHERE id = %s"
    
    try:
        cursor.execute(query, valores)
        conn.commit()
        
        # Obtener el usuario actualizado
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        usuario_actualizado_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Usuario actualizado: ID {usuario_id}")
        
        return UsuarioResponse(
            id=usuario_actualizado_result[0],
            nombre=usuario_actualizado_result[1],
            email=usuario_actualizado_result[2],
            telefono=usuario_actualizado_result[3],
            direccion=usuario_actualizado_result[4],
            tipo_usuario=usuario_actualizado_result[5],
            activo=usuario_actualizado_result[6],
            fecha_registro=str(usuario_actualizado_result[7])
        )
    except mysql.connector.IntegrityError as e:
        cursor.close()
        conn.close()
        logger.error(f"Error de integridad al actualizar usuario: {e}")
        raise HTTPException(status_code=400, detail="El email ya está registrado por otro usuario")
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al actualizar usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {e}")

# DELETE - Eliminar usuario por ID
@app.delete("/usuarios/{usuario_id}", tags=["Usuarios"])
def eliminar_usuario(usuario_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el usuario existe
    cursor.execute("SELECT nombre, email FROM usuarios WHERE id = %s", (usuario_id,))
    usuario_existente = cursor.fetchone()
    if not usuario_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si el usuario tiene préstamos activos
    cursor.execute("""
        SELECT COUNT(*) as activos 
        FROM prestamos 
        WHERE usuario_id = %s AND estado = 'activo'
    """, (usuario_id,))
    prestamos_activos = cursor.fetchone()[0]
    
    if prestamos_activos > 0:
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el usuario porque tiene {prestamos_activos} préstamo(s) activo(s)"
        )
    
    try:
        # Eliminar el usuario (esto también eliminará automáticamente los préstamos y reseñas asociadas por CASCADE)
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Usuario eliminado: '{usuario_existente[0]}' ({usuario_existente[1]}) (ID: {usuario_id})")
        
        return {
            "mensaje": "Usuario eliminado exitosamente",
            "usuario_eliminado": {
                "id": usuario_id,
                "nombre": usuario_existente[0],
                "email": usuario_existente[1]
            }
        }
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al eliminar usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {e}")

# =============================================================================
# ENDPOINTS PRÉSTAMOS
# =============================================================================

# CREATE - Crear préstamo
@app.post("/prestamos/", response_model=PrestamoResponse, tags=["Préstamos"])
def crear_prestamo(prestamo: Prestamo):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el libro existe
    cursor.execute("SELECT titulo FROM libros WHERE id = %s", (prestamo.libro_id,))
    libro = cursor.fetchone()
    if not libro:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Verificar que el usuario existe
    cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (prestamo.usuario_id,))
    usuario = cursor.fetchone()
    if not usuario:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que el libro no esté ya prestado
    cursor.execute("""
        SELECT id FROM prestamos 
        WHERE libro_id = %s AND estado = 'activo'
    """, (prestamo.libro_id,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El libro ya está prestado")
    
    query = """
        INSERT INTO prestamos (libro_id, usuario_id, fecha_devolucion_esperada) 
        VALUES (%s, %s, %s)
    """
    values = (prestamo.libro_id, prestamo.usuario_id, prestamo.fecha_devolucion_esperada)
    
    try:
        cursor.execute(query, values)
        conn.commit()
        prestamo_id = cursor.lastrowid
        
        # Obtener el préstamo creado con información relacionada
        cursor.execute("""
            SELECT p.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
            FROM prestamos p
            JOIN libros l ON p.libro_id = l.id
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = %s
        """, (prestamo_id,))
        prestamo_creado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Préstamo creado: Libro '{libro[0]}' para usuario '{usuario[0]}'")
        
        return PrestamoResponse(
            id=prestamo_creado[0],
            libro_id=prestamo_creado[1],
            usuario_id=prestamo_creado[2],
            fecha_prestamo=str(prestamo_creado[3]),
            fecha_devolucion_esperada=str(prestamo_creado[4]),
            fecha_devolucion_real=str(prestamo_creado[5]) if prestamo_creado[5] else None,
            estado=prestamo_creado[6],
            libro_titulo=prestamo_creado[7],
            usuario_nombre=prestamo_creado[8]
        )
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al crear préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear préstamo: {e}")

# READ - Obtener préstamos con paginación
@app.get("/prestamos/", response_model=PaginatedPrestamosResponse, tags=["Préstamos"])
def obtener_prestamos(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Préstamos por página"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (activo, devuelto, vencido)"),
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Construir query base con JOINs
    query = """
        SELECT p.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
        FROM prestamos p
        JOIN libros l ON p.libro_id = l.id
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    
    # Aplicar filtros
    if estado:
        query += " AND p.estado = %s"
        params.append(estado)
    
    # Contar total
    count_query = query.replace("SELECT p.*, l.titulo as libro_titulo, u.nombre as usuario_nombre", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total = cursor.fetchone()['COUNT(*)']
    
    # Aplicar ordenamiento
    query += " ORDER BY p.fecha_prestamo DESC"
    
    # Aplicar paginación
    offset = (pagina - 1) * por_pagina
    query += " LIMIT %s OFFSET %s"
    params.extend([por_pagina, offset])
    
    cursor.execute(query, params)
    prestamos_raw = cursor.fetchall()
    
    # Convertir datetime a string
    prestamos = []
    for prestamo in prestamos_raw:
        prestamo_dict = dict(prestamo)
        if prestamo_dict.get('fecha_prestamo'):
            prestamo_dict['fecha_prestamo'] = str(prestamo_dict['fecha_prestamo'])
        if prestamo_dict.get('fecha_devolucion_esperada'):
            prestamo_dict['fecha_devolucion_esperada'] = str(prestamo_dict['fecha_devolucion_esperada'])
        if prestamo_dict.get('fecha_devolucion_real'):
            prestamo_dict['fecha_devolucion_real'] = str(prestamo_dict['fecha_devolucion_real'])
        prestamos.append(prestamo_dict)
    
    cursor.close()
    conn.close()
    
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return PaginatedPrestamosResponse(
        prestamos=prestamos,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas
    )

# READ - Obtener préstamo por ID
@app.get("/prestamos/{prestamo_id}", response_model=PrestamoResponse, tags=["Préstamos"])
def obtener_prestamo(prestamo_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
        FROM prestamos p
        JOIN libros l ON p.libro_id = l.id
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = %s
    """, (prestamo_id,))
    prestamo = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # Convertir datetime a string
    prestamo_dict = dict(prestamo)
    if prestamo_dict.get('fecha_prestamo'):
        prestamo_dict['fecha_prestamo'] = str(prestamo_dict['fecha_prestamo'])
    if prestamo_dict.get('fecha_devolucion_esperada'):
        prestamo_dict['fecha_devolucion_esperada'] = str(prestamo_dict['fecha_devolucion_esperada'])
    if prestamo_dict.get('fecha_devolucion_real'):
        prestamo_dict['fecha_devolucion_real'] = str(prestamo_dict['fecha_devolucion_real'])
    
    return prestamo_dict

# UPDATE - Editar préstamo por ID
@app.put("/prestamos/{prestamo_id}", response_model=PrestamoResponse, tags=["Préstamos"])
def editar_prestamo(prestamo_id: int, prestamo_actualizado: PrestamoUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el préstamo existe
    cursor.execute("SELECT * FROM prestamos WHERE id = %s", (prestamo_id,))
    prestamo_existente = cursor.fetchone()
    if not prestamo_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # Construir query de actualización solo con campos proporcionados
    campos_actualizar = []
    valores = []
    
    if prestamo_actualizado.fecha_devolucion_esperada is not None:
        campos_actualizar.append("fecha_devolucion_esperada = %s")
        valores.append(prestamo_actualizado.fecha_devolucion_esperada)
    
    if prestamo_actualizado.estado is not None:
        # Validar que el estado sea válido
        estados_validos = ['activo', 'devuelto', 'vencido']
        if prestamo_actualizado.estado not in estados_validos:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail=f"Estado inválido. Estados válidos: {estados_validos}")
        
        campos_actualizar.append("estado = %s")
        valores.append(prestamo_actualizado.estado)
        
        # Si se marca como devuelto, actualizar fecha de devolución real
        if prestamo_actualizado.estado == 'devuelto':
            campos_actualizar.append("fecha_devolucion_real = CURDATE()")
    
    # Si no hay campos para actualizar
    if not campos_actualizar:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    # Ejecutar actualización
    valores.append(prestamo_id)
    query = f"UPDATE prestamos SET {', '.join(campos_actualizar)} WHERE id = %s"
    
    try:
        cursor.execute(query, valores)
        conn.commit()
        
        # Obtener el préstamo actualizado con información relacionada
        cursor.execute("""
            SELECT p.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
            FROM prestamos p
            JOIN libros l ON p.libro_id = l.id
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = %s
        """, (prestamo_id,))
        prestamo_actualizado_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Préstamo actualizado: ID {prestamo_id}")
        
        return PrestamoResponse(
            id=prestamo_actualizado_result[0],
            libro_id=prestamo_actualizado_result[1],
            usuario_id=prestamo_actualizado_result[2],
            fecha_prestamo=str(prestamo_actualizado_result[3]),
            fecha_devolucion_esperada=str(prestamo_actualizado_result[4]),
            fecha_devolucion_real=str(prestamo_actualizado_result[5]) if prestamo_actualizado_result[5] else None,
            estado=prestamo_actualizado_result[6],
            libro_titulo=prestamo_actualizado_result[7],
            usuario_nombre=prestamo_actualizado_result[8]
        )
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al actualizar préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar préstamo: {e}")

# DELETE - Eliminar préstamo por ID
@app.delete("/prestamos/{prestamo_id}", tags=["Préstamos"])
def eliminar_prestamo(prestamo_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el préstamo existe y obtener información
    cursor.execute("""
        SELECT p.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
        FROM prestamos p
        JOIN libros l ON p.libro_id = l.id
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = %s
    """, (prestamo_id,))
    prestamo_existente = cursor.fetchone()
    if not prestamo_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    # Verificar si el préstamo está activo (advertencia, pero permitir eliminación)
    estado_prestamo = prestamo_existente[6]  # estado está en índice 6
    
    try:
        # Eliminar el préstamo
        cursor.execute("DELETE FROM prestamos WHERE id = %s", (prestamo_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Préstamo eliminado: ID {prestamo_id} - '{prestamo_existente[7]}' para '{prestamo_existente[8]}'")
        
        return {
            "mensaje": "Préstamo eliminado exitosamente",
            "prestamo_eliminado": {
                "id": prestamo_id,
                "libro_titulo": prestamo_existente[7],
                "usuario_nombre": prestamo_existente[8],
                "estado": estado_prestamo,
                "advertencia": "Se eliminó un préstamo activo" if estado_prestamo == 'activo' else None
            }
        }
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al eliminar préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar préstamo: {e}")

# =============================================================================
# ENDPOINTS RESEÑAS
# =============================================================================

# CREATE - Crear reseña
@app.post("/reseñas/", response_model=ReseñaResponse, tags=["Reseñas"])
def crear_reseña(reseña: Reseña):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el libro existe
    cursor.execute("SELECT titulo FROM libros WHERE id = %s", (reseña.libro_id,))
    libro = cursor.fetchone()
    if not libro:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Verificar que el usuario existe
    cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (reseña.usuario_id,))
    usuario = cursor.fetchone()
    if not usuario:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    query = """
        INSERT INTO reseñas (libro_id, usuario_id, calificacion, comentario) 
        VALUES (%s, %s, %s, %s)
    """
    values = (reseña.libro_id, reseña.usuario_id, reseña.calificacion, reseña.comentario)
    
    try:
        cursor.execute(query, values)
        conn.commit()
        reseña_id = cursor.lastrowid
        
        # Obtener la reseña creada con información relacionada
        cursor.execute("""
            SELECT r.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
            FROM reseñas r
            JOIN libros l ON r.libro_id = l.id
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.id = %s
        """, (reseña_id,))
        reseña_creada = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Reseña creada: {reseña.calificacion}/5 para '{libro[0]}' por '{usuario[0]}'")
        
        return ReseñaResponse(
            id=reseña_creada[0],
            libro_id=reseña_creada[1],
            usuario_id=reseña_creada[2],
            calificacion=reseña_creada[3],
            comentario=reseña_creada[4],
            fecha_reseña=str(reseña_creada[5]),
            libro_titulo=reseña_creada[6],
            usuario_nombre=reseña_creada[7]
        )
    except mysql.connector.IntegrityError as e:
        cursor.close()
        conn.close()
        logger.error(f"Error de integridad al crear reseña: {e}")
        raise HTTPException(status_code=400, detail="El usuario ya ha reseñado este libro")
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al crear reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear reseña: {e}")

# READ - Obtener reseñas con paginación
@app.get("/reseñas/", response_model=PaginatedReseñasResponse, tags=["Reseñas"])
def obtener_reseñas(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Reseñas por página"),
    libro_id: Optional[int] = Query(None, description="Filtrar por libro"),
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Construir query base con JOINs
    query = """
        SELECT r.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
        FROM reseñas r
        JOIN libros l ON r.libro_id = l.id
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE 1=1
    """
    params = []
    
    # Aplicar filtros
    if libro_id:
        query += " AND r.libro_id = %s"
        params.append(libro_id)
    
    # Contar total
    count_query = query.replace("SELECT r.*, l.titulo as libro_titulo, u.nombre as usuario_nombre", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total = cursor.fetchone()['COUNT(*)']
    
    # Aplicar ordenamiento
    query += " ORDER BY r.fecha_reseña DESC"
    
    # Aplicar paginación
    offset = (pagina - 1) * por_pagina
    query += " LIMIT %s OFFSET %s"
    params.extend([por_pagina, offset])
    
    cursor.execute(query, params)
    reseñas_raw = cursor.fetchall()
    
    # Convertir datetime a string
    reseñas = []
    for reseña in reseñas_raw:
        reseña_dict = dict(reseña)
        if reseña_dict.get('fecha_reseña'):
            reseña_dict['fecha_reseña'] = str(reseña_dict['fecha_reseña'])
        reseñas.append(reseña_dict)
    
    cursor.close()
    conn.close()
    
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return PaginatedReseñasResponse(
        reseñas=reseñas,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas
    )

# READ - Obtener reseña por ID
@app.get("/reseñas/{reseña_id}", response_model=ReseñaResponse, tags=["Reseñas"])
def obtener_reseña(reseña_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT r.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
        FROM reseñas r
        JOIN libros l ON r.libro_id = l.id
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE r.id = %s
    """, (reseña_id,))
    reseña = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not reseña:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    
    # Convertir datetime a string
    reseña_dict = dict(reseña)
    if reseña_dict.get('fecha_reseña'):
        reseña_dict['fecha_reseña'] = str(reseña_dict['fecha_reseña'])
    
    return reseña_dict

# UPDATE - Editar reseña por ID
@app.put("/reseñas/{reseña_id}", response_model=ReseñaResponse, tags=["Reseñas"])
def editar_reseña(reseña_id: int, reseña_actualizada: ReseñaUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la reseña existe
    cursor.execute("SELECT usuario_id FROM reseñas WHERE id = %s", (reseña_id,))
    reseña_existente = cursor.fetchone()
    if not reseña_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    
    # Construir query de actualización solo con campos proporcionados
    campos_actualizar = []
    valores = []
    
    if reseña_actualizada.calificacion is not None:
        # Validar calificación
        if reseña_actualizada.calificacion < 1 or reseña_actualizada.calificacion > 5:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="La calificación debe estar entre 1 y 5")
        
        campos_actualizar.append("calificacion = %s")
        valores.append(reseña_actualizada.calificacion)
    
    if reseña_actualizada.comentario is not None:
        campos_actualizar.append("comentario = %s")
        valores.append(reseña_actualizada.comentario)
    
    # Si no hay campos para actualizar
    if not campos_actualizar:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    # Ejecutar actualización
    valores.append(reseña_id)
    query = f"UPDATE reseñas SET {', '.join(campos_actualizar)} WHERE id = %s"
    
    try:
        cursor.execute(query, valores)
        conn.commit()
        
        # Obtener la reseña actualizada con información relacionada
        cursor.execute("""
            SELECT r.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
            FROM reseñas r
            JOIN libros l ON r.libro_id = l.id
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.id = %s
        """, (reseña_id,))
        reseña_actualizada_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Reseña actualizada: ID {reseña_id}")
        
        return ReseñaResponse(
            id=reseña_actualizada_result[0],
            libro_id=reseña_actualizada_result[1],
            usuario_id=reseña_actualizada_result[2],
            calificacion=reseña_actualizada_result[3],
            comentario=reseña_actualizada_result[4],
            fecha_reseña=str(reseña_actualizada_result[5]),
            libro_titulo=reseña_actualizada_result[6],
            usuario_nombre=reseña_actualizada_result[7]
        )
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al actualizar reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar reseña: {e}")

# DELETE - Eliminar reseña por ID
@app.delete("/reseñas/{reseña_id}", tags=["Reseñas"])
def eliminar_reseña(reseña_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la reseña existe y obtener información
    cursor.execute("""
        SELECT r.*, l.titulo as libro_titulo, u.nombre as usuario_nombre
        FROM reseñas r
        JOIN libros l ON r.libro_id = l.id
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE r.id = %s
    """, (reseña_id,))
    reseña_existente = cursor.fetchone()
    if not reseña_existente:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    
    try:
        # Eliminar la reseña
        cursor.execute("DELETE FROM reseñas WHERE id = %s", (reseña_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Reseña eliminada: ID {reseña_id} - {reseña_existente[3]}/5 para '{reseña_existente[6]}' por '{reseña_existente[7]}'")
        
        return {
            "mensaje": "Reseña eliminada exitosamente",
            "reseña_eliminada": {
                "id": reseña_id,
                "libro_titulo": reseña_existente[6],
                "usuario_nombre": reseña_existente[7],
                "calificacion": reseña_existente[3],
                "comentario": reseña_existente[4] if reseña_existente[4] else "Sin comentario"
            }
        }
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        logger.error(f"Error al eliminar reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar reseña: {e}")

# ESTADÍSTICAS COMPLETAS
@app.get("/estadisticas/", response_model=Estadisticas, tags=["Estadísticas"])
def obtener_estadisticas():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Total de libros
    cursor.execute("SELECT COUNT(*) as total FROM libros")
    total_libros = cursor.fetchone()['total']
    
    # Total de usuarios
    cursor.execute("SELECT COUNT(*) as total FROM usuarios")
    total_usuarios = cursor.fetchone()['total']
    
    # Total de préstamos
    cursor.execute("SELECT COUNT(*) as total FROM prestamos")
    total_prestamos = cursor.fetchone()['total']
    
    # Total de reseñas
    cursor.execute("SELECT COUNT(*) as total FROM reseñas")
    total_reseñas = cursor.fetchone()['total']
    
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
    
    # Usuarios por tipo
    cursor.execute("""
        SELECT tipo_usuario, COUNT(*) as cantidad 
        FROM usuarios 
        GROUP BY tipo_usuario 
        ORDER BY cantidad DESC
    """)
    usuarios_por_tipo = {row['tipo_usuario']: row['cantidad'] for row in cursor.fetchall()}
    
    # Préstamos activos
    cursor.execute("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'activo'")
    prestamos_activos = cursor.fetchone()['total']
    
    # Préstamos vencidos
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM prestamos 
        WHERE estado = 'activo' AND fecha_devolucion_esperada < CURDATE()
    """)
    prestamos_vencidos = cursor.fetchone()['total']
    
    # Promedio de calificaciones
    cursor.execute("SELECT AVG(calificacion) as promedio FROM reseñas")
    promedio_result = cursor.fetchone()['promedio']
    promedio_calificaciones = float(promedio_result) if promedio_result else 0.0
    
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
        total_usuarios=total_usuarios,
        total_prestamos=total_prestamos,
        total_reseñas=total_reseñas,
        libros_por_genero=libros_por_genero,
        libros_por_año=libros_por_año,
        usuarios_por_tipo=usuarios_por_tipo,
        prestamos_activos=prestamos_activos,
        prestamos_vencidos=prestamos_vencidos,
        promedio_calificaciones=round(promedio_calificaciones, 2),
        autores_unicos=autores_unicos,
        generos_unicos=generos_unicos
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)