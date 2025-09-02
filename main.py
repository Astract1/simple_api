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

    
# Función helper para ObjectId
def str_to_objectid(id_str: str) -> ObjectId:
    if not id_str or not isinstance(id_str, str) or len(id_str) != 24:
        raise HTTPException(status_code=400, detail="ID inválido: debe ser un ObjectId válido de 24 caracteres hexadecimales")
    try:
        return ObjectId(id_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ID inválido: {str(e)}")

# Función para validar email
def validar_email(email: str) -> bool:
    import re
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

# Función para validar telefono
def validar_telefono(telefono: str) -> bool:
    if not telefono:
        return True  # Es opcional
    import re
    patron = r'^\+?[0-9\s\-\(\)]{7,15}$'
    return re.match(patron, telefono) is not None

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

class LibroResponse(BaseModel):
    id: str = Field(alias="_id")
    titulo: str
    autor: str
    año: int
    genero: Optional[str] = None
    isbn: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_creacion: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class LibroUpdate(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    año: Optional[int] = None
    genero: Optional[str] = None
    isbn: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('titulo')
    @classmethod
    def validar_titulo(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('El título no puede estar vacío')
        return v.strip() if v else v
    
    @field_validator('autor')
    @classmethod
    def validar_autor(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('El autor no puede estar vacío')
        return v.strip() if v else v
    
    @field_validator('año')
    @classmethod
    def validar_año(cls, v):
        if v is not None and (v < 1000 or v > datetime.now().year):
            raise ValueError(f'El año debe estar entre 1000 y {datetime.now().year}')
        return v
    
    @field_validator('genero')
    @classmethod
    def validar_genero(cls, v):
        return v.strip() if v else v
    
    @field_validator('isbn')
    @classmethod
    def validar_isbn(cls, v):
        return v.strip() if v else v
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        return v.strip() if v else v

# Modelos Pydantic - USUARIOS
class Usuario(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo")
    email: str = Field(..., max_length=150, description="Correo electrónico")
    telefono: Optional[str] = Field(None, max_length=15, description="Número de teléfono")
    direccion: Optional[str] = Field(None, max_length=300, description="Dirección")
    tipo_usuario: str = Field("estudiante", description="Tipo de usuario (estudiante, profesor, administrador)")
    
    @field_validator('email')
    @classmethod
    def validar_email_format(cls, v):
        if not validar_email(v):
            raise ValueError('Formato de email inválido')
        return v.lower().strip()
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono_format(cls, v):
        if v and not validar_telefono(v):
            raise ValueError('Formato de teléfono inválido')
        return v.strip() if v else None
    
    @field_validator('tipo_usuario')
    @classmethod
    def validar_tipo_usuario(cls, v):
        tipos_validos = ['estudiante', 'profesor', 'administrador']
        if v and v.strip() and v not in tipos_validos:
            raise ValueError(f'Tipo de usuario debe ser uno de: {tipos_validos}')
        return v if v and v.strip() else 'estudiante'  # Valor por defecto
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class UsuarioResponse(BaseModel):
    id: str = Field(alias="_id")
    nombre: str
    email: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_usuario: str = "estudiante"
    activo: bool = True
    fecha_registro: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_usuario: Optional[str] = None
    activo: Optional[bool] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        # Solo validar si se proporciona un valor no vacío
        if v is not None and v.strip() == "":
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v
    
    @field_validator('email')
    @classmethod
    def validar_email_format(cls, v):
        # Solo validar si se proporciona un valor no vacío
        if v is not None and v.strip():
            if not validar_email(v.strip()):
                raise ValueError('Formato de email inválido')
            return v.lower().strip()
        return v
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono_format(cls, v):
        # Solo validar si se proporciona un valor no vacío
        if v is not None and v.strip():
            if not validar_telefono(v.strip()):
                raise ValueError('Formato de teléfono inválido')
            return v.strip()
        return v
    
    @field_validator('tipo_usuario')
    @classmethod
    def validar_tipo_usuario(cls, v):
        # Solo validar si se proporciona un valor no vacío
        if v is not None and v.strip():
            tipos_validos = ['estudiante', 'profesor', 'administrador']
            if v.strip() not in tipos_validos:
                raise ValueError(f'Tipo de usuario debe ser uno de: {tipos_validos}')
            return v.strip()
        return v

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

class ReseñaResponse(BaseModel):
    id: str = Field(alias="_id")
    libro_id: str
    usuario_id: str
    calificacion: int
    comentario: Optional[str] = None
    fecha_reseña: str
    libro_titulo: Optional[str] = None
    usuario_nombre: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ReseñaUpdate(BaseModel):
    calificacion: Optional[int] = None
    comentario: Optional[str] = None
    
    @field_validator('calificacion')
    @classmethod
    def validar_calificacion(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('La calificación debe estar entre 1 y 5')
        return v
    
    @field_validator('comentario')
    @classmethod
    def validar_comentario(cls, v):
        return v.strip() if v else v

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
        
        logger.info("✅ Base de datos poblada exitosamente con:")
        logger.info(f"   📚 {len(libros_data)} libros")
        logger.info(f"   👥 {len(usuarios_data)} usuarios") 
        
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
        # Validaciones adicionales
        if not libro.titulo.strip():
            raise HTTPException(status_code=400, detail="El título no puede estar vacío")
        if not libro.autor.strip():
            raise HTTPException(status_code=400, detail="El autor no puede estar vacío")
        
        # Verificar si ya existe un libro con el mismo título y autor
        libro_existente = await db.libros.find_one({
            "titulo": {"$regex": f"^{libro.titulo.strip()}$", "$options": "i"},
            "autor": {"$regex": f"^{libro.autor.strip()}$", "$options": "i"}
        })
        if libro_existente:
            raise HTTPException(status_code=400, detail="Ya existe un libro con el mismo título y autor")
        
        # Validar ISBN único si se proporciona
        if libro.isbn and libro.isbn.strip():
            isbn_existente = await db.libros.find_one({"isbn": libro.isbn.strip()})
            if isbn_existente:
                raise HTTPException(status_code=400, detail="Ya existe un libro con este ISBN")
        
        libro_doc = {
            "titulo": libro.titulo.strip(),
            "autor": libro.autor.strip(),
            "año": libro.año,
            "genero": libro.genero.strip() if libro.genero else None,
            "isbn": libro.isbn.strip() if libro.isbn else None,
            "descripcion": libro.descripcion.strip() if libro.descripcion else None,
            "fecha_creacion": datetime.now()
        }
        
        result = await db.libros.insert_one(libro_doc)
        libro_creado = await db.libros.find_one({"_id": result.inserted_id})
        
        logger.info(f"Libro creado: {libro.titulo} por {libro.autor}")
        
        libro_creado["_id"] = str(libro_creado["_id"])
        if libro_creado.get("fecha_creacion"):
            libro_creado["fecha_creacion"] = str(libro_creado["fecha_creacion"])
        
        return LibroResponse(**libro_creado)
    except HTTPException:
        raise
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
    try:
        # Construir filtro
        filtro = {}
        
        if genero:
            filtro["genero"] = genero
        
        if año_min:
            filtro.setdefault("año", {})["$gte"] = año_min
        
        if año_max:
            filtro.setdefault("año", {})["$lte"] = año_max
        
        # Contar total
        total = await db.libros.count_documents(filtro)
        
        # Aplicar ordenamiento
        campos_validos = ['_id', 'titulo', 'autor', 'año', 'genero']
        if ordenar_por not in campos_validos:
            ordenar_por = '_id'
        
        direccion = ASCENDING if orden.lower() == 'asc' else DESCENDING
        
        # Aplicar paginación
        skip = (pagina - 1) * por_pagina
        
        cursor = db.libros.find(filtro).sort(ordenar_por, direccion).skip(skip).limit(por_pagina)
        libros_raw = await cursor.to_list(length=por_pagina)
        
        # Convertir ObjectId a string y formatear fechas
        libros = []
        for libro in libros_raw:
            libro["_id"] = str(libro["_id"])
            if libro.get("fecha_creacion"):
                libro["fecha_creacion"] = str(libro["fecha_creacion"])
            libros.append(LibroResponse(**libro))
        
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return PaginatedResponse(
            libros=libros,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas
        )
    except Exception as e:
        logger.error(f"Error al obtener libros: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener libros: {e}")

# READ - Obtener libro por ID
@app.get("/libros/{libro_id}", response_model=LibroResponse, tags=["Libros"])
async def obtener_libro(libro_id: str):
    try:
        object_id = str_to_objectid(libro_id)
        libro = await db.libros.find_one({"_id": object_id})
        
        if not libro:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        libro["_id"] = str(libro["_id"])
        if libro.get("fecha_creacion"):
            libro["fecha_creacion"] = str(libro["fecha_creacion"])
        
        return LibroResponse(**libro)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener libro: {e}")

# UPDATE - Editar libro por ID
@app.put("/libros/{libro_id}", response_model=LibroResponse, tags=["Libros"])
async def editar_libro(libro_id: str, libro_actualizado: LibroUpdate):
    try:
        # Validar ObjectId
        object_id = str_to_objectid(libro_id)
        
        # Verificar que el libro existe
        libro_existente = await db.libros.find_one({"_id": object_id})
        if not libro_existente:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Construir actualización solo con campos proporcionados (validados por Pydantic)
        actualizacion = {}
        
        if libro_actualizado.titulo is not None:
            # Verificar duplicado de título-autor si se actualiza el título
            titulo_autor_existente = await db.libros.find_one({
                "titulo": {"$regex": f"^{libro_actualizado.titulo.strip()}$", "$options": "i"},
                "autor": libro_existente["autor"],
                "_id": {"$ne": object_id}
            })
            if titulo_autor_existente:
                raise HTTPException(status_code=400, detail="Ya existe otro libro con este título del mismo autor")
            actualizacion["titulo"] = libro_actualizado.titulo
            
        if libro_actualizado.autor is not None:
            # Verificar duplicado de título-autor si se actualiza el autor
            titulo_autor_existente = await db.libros.find_one({
                "titulo": libro_existente["titulo"],
                "autor": {"$regex": f"^{libro_actualizado.autor.strip()}$", "$options": "i"},
                "_id": {"$ne": object_id}
            })
            if titulo_autor_existente:
                raise HTTPException(status_code=400, detail="Ya existe otro libro con este autor del mismo título")
            actualizacion["autor"] = libro_actualizado.autor
            
        if libro_actualizado.año is not None:
            actualizacion["año"] = libro_actualizado.año
            
        if libro_actualizado.genero is not None:
            actualizacion["genero"] = libro_actualizado.genero
            
        if libro_actualizado.isbn is not None:
            # Verificar ISBN único si se proporciona
            if libro_actualizado.isbn and libro_actualizado.isbn.strip():
                isbn_existente = await db.libros.find_one({
                    "isbn": libro_actualizado.isbn.strip(),
                    "_id": {"$ne": object_id}
                })
                if isbn_existente:
                    raise HTTPException(status_code=400, detail="Ya existe otro libro con este ISBN")
            actualizacion["isbn"] = libro_actualizado.isbn
            
        if libro_actualizado.descripcion is not None:
            actualizacion["descripcion"] = libro_actualizado.descripcion
        
        if not actualizacion:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos válidos para actualizar")
        
        # Ejecutar actualización SOLO en el documento específico
        logger.info(f"Actualizando libro con ID: {libro_id}, campos: {list(actualizacion.keys())}")
        
        resultado = await db.libros.update_one(
            {"_id": object_id},  # Filtro exacto por ObjectId
            {"$set": actualizacion}  # Solo actualizar los campos especificados
        )
        
        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Libro no encontrado para actualizar")
        
        if resultado.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se realizaron cambios en el libro")
        
        # Obtener el libro actualizado
        libro_actualizado_result = await db.libros.find_one({"_id": object_id})
        
        if not libro_actualizado_result:
            raise HTTPException(status_code=500, detail="Error al obtener el libro actualizado")
        
        logger.info(f"Libro actualizado exitosamente: ID {libro_id}")
        
        # Convertir ObjectId a string
        libro_actualizado_result["_id"] = str(libro_actualizado_result["_id"])
        if libro_actualizado_result.get("fecha_creacion"):
            libro_actualizado_result["fecha_creacion"] = str(libro_actualizado_result["fecha_creacion"])
        
        return LibroResponse(**libro_actualizado_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar libro: {e}")

# DELETE - Eliminar libro por ID
@app.delete("/libros/{libro_id}", tags=["Libros"])
async def eliminar_libro(libro_id: str):
    try:
        object_id = str_to_objectid(libro_id)
        
        # Verificar que el libro existe
        libro_existente = await db.libros.find_one({"_id": object_id})
        if not libro_existente:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Verificar si el libro tiene préstamos activos
        prestamos_activos = await db.prestamos.count_documents({"libro_id": libro_id, "estado": "activo"})
        
        if prestamos_activos > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar el libro porque tiene {prestamos_activos} préstamo(s) activo(s)"
            )
        
        # Eliminar el libro
        await db.libros.delete_one({"_id": object_id})
        # Eliminar préstamos y reseñas asociadas
        await db.prestamos.delete_many({"libro_id": libro_id})
        await db.reseñas.delete_many({"libro_id": libro_id})
        
        logger.info(f"Libro eliminado: '{libro_existente['titulo']}' por {libro_existente['autor']} (ID: {libro_id})")
        
        return {
            "mensaje": "Libro eliminado exitosamente",
            "libro_eliminado": {
                "id": libro_id,
                "titulo": libro_existente["titulo"],
                "autor": libro_existente["autor"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar libro: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar libro: {e}")

# =============================================================================
# ENDPOINTS USUARIOS
# =============================================================================

# CREATE - Crear usuario
@app.post("/usuarios/", response_model=UsuarioResponse, tags=["Usuarios"])
async def crear_usuario(usuario: Usuario):
    try:
        # Verificar que el email no existe (sin distinguir mayúsculas/minúsculas)
        usuario_existente = await db.usuarios.find_one({"email": usuario.email.lower()})
        if usuario_existente:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Validar tipo de usuario
        tipos_validos = ['estudiante', 'profesor', 'administrador']
        if usuario.tipo_usuario not in tipos_validos:
            raise HTTPException(status_code=400, detail=f"Tipo de usuario inválido. Tipos válidos: {tipos_validos}")
        
        usuario_doc = {
            "nombre": usuario.nombre.strip(),
            "email": usuario.email.lower().strip(),
            "telefono": usuario.telefono.strip() if usuario.telefono else None,
            "direccion": usuario.direccion.strip() if usuario.direccion else None,
            "tipo_usuario": usuario.tipo_usuario,
            "activo": True,
            "fecha_registro": datetime.now()
        }
        
        result = await db.usuarios.insert_one(usuario_doc)
        usuario_creado = await db.usuarios.find_one({"_id": result.inserted_id})
        
        logger.info(f"Usuario creado: {usuario.nombre} ({usuario.email})")
        
        usuario_creado["_id"] = str(usuario_creado["_id"])
        if usuario_creado.get("fecha_registro"):
            usuario_creado["fecha_registro"] = str(usuario_creado["fecha_registro"])
        
        return UsuarioResponse(**usuario_creado)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {e}")

# READ - Obtener usuarios con paginación y filtros
@app.get("/usuarios/", response_model=PaginatedUsuariosResponse, tags=["Usuarios"])
async def obtener_usuarios(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Usuarios por página"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo de usuario"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo")
):
    try:
        # Construir filtro
        filtro = {}
        
        if tipo_usuario:
            tipos_validos = ['estudiante', 'profesor', 'administrador']
            if tipo_usuario not in tipos_validos:
                raise HTTPException(status_code=400, detail=f"Tipo de usuario inválido. Tipos válidos: {tipos_validos}")
            filtro["tipo_usuario"] = tipo_usuario
        
        if activo is not None:
            filtro["activo"] = activo
        
        # Contar total
        total = await db.usuarios.count_documents(filtro)
        
        # Aplicar paginación
        skip = (pagina - 1) * por_pagina
        
        cursor = db.usuarios.find(filtro).sort("fecha_registro", DESCENDING).skip(skip).limit(por_pagina)
        usuarios_raw = await cursor.to_list(length=por_pagina)
        
        # Convertir ObjectId a string y formatear fechas
        usuarios = []
        for usuario in usuarios_raw:
            usuario["_id"] = str(usuario["_id"])
            if usuario.get("fecha_registro"):
                usuario["fecha_registro"] = str(usuario["fecha_registro"])
            usuarios.append(UsuarioResponse(**usuario))
        
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return PaginatedUsuariosResponse(
            usuarios=usuarios,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {e}")

# READ - Obtener usuario por ID
@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuarios"])
async def obtener_usuario(usuario_id: str):
    try:
        object_id = str_to_objectid(usuario_id)
        usuario = await db.usuarios.find_one({"_id": object_id})
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        usuario["_id"] = str(usuario["_id"])
        if usuario.get("fecha_registro"):
            usuario["fecha_registro"] = str(usuario["fecha_registro"])
        
        return UsuarioResponse(**usuario)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {e}")

# UPDATE - Editar usuario por ID
@app.put("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuarios"])
async def editar_usuario(usuario_id: str, usuario_actualizado: UsuarioUpdate):
    try:
        # Validar ObjectId
        object_id = str_to_objectid(usuario_id)
        
        # Verificar que el usuario existe
        usuario_existente = await db.usuarios.find_one({"_id": object_id})
        if not usuario_existente:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Construir actualización solo con campos proporcionados (validados por Pydantic)
        actualizacion = {}
        
        if usuario_actualizado.nombre is not None:
            actualizacion["nombre"] = usuario_actualizado.nombre
            
        if usuario_actualizado.email is not None:
            # Verificación adicional: email no debe existir en otro usuario
            if usuario_actualizado.email:  # Solo si no es cadena vacía
                email_existente = await db.usuarios.find_one({
                    "email": usuario_actualizado.email,
                    "_id": {"$ne": object_id}
                })
                if email_existente:
                    raise HTTPException(status_code=400, detail="El email ya está registrado por otro usuario")
            actualizacion["email"] = usuario_actualizado.email
            
        if usuario_actualizado.telefono is not None:
            actualizacion["telefono"] = usuario_actualizado.telefono
            
        if usuario_actualizado.direccion is not None:
            actualizacion["direccion"] = usuario_actualizado.direccion
            
        if usuario_actualizado.tipo_usuario is not None:
            actualizacion["tipo_usuario"] = usuario_actualizado.tipo_usuario
            
        if usuario_actualizado.activo is not None:
            actualizacion["activo"] = usuario_actualizado.activo
        
        if not actualizacion:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos válidos para actualizar")
        
        # Ejecutar actualización SOLO en el documento específico
        logger.info(f"Actualizando usuario con ID: {usuario_id}, campos: {list(actualizacion.keys())}")
        
        resultado = await db.usuarios.update_one(
            {"_id": object_id},
            {"$set": actualizacion}
        )
        
        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado para actualizar")
            
        if resultado.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se realizaron cambios en el usuario")
        
        # Obtener el usuario actualizado
        usuario_actualizado_result = await db.usuarios.find_one({"_id": object_id})
        
        logger.info(f"Usuario actualizado exitosamente: ID {usuario_id}")
        
        usuario_actualizado_result["_id"] = str(usuario_actualizado_result["_id"])
        if usuario_actualizado_result.get("fecha_registro"):
            usuario_actualizado_result["fecha_registro"] = str(usuario_actualizado_result["fecha_registro"])
        
        return UsuarioResponse(**usuario_actualizado_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {e}")

# DELETE - Eliminar usuario por ID
@app.delete("/usuarios/{usuario_id}", tags=["Usuarios"])
async def eliminar_usuario(usuario_id: str):
    try:
        object_id = str_to_objectid(usuario_id)
        
        # Verificar que el usuario existe
        usuario_existente = await db.usuarios.find_one({"_id": object_id})
        if not usuario_existente:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar si el usuario tiene préstamos activos
        prestamos_activos = await db.prestamos.count_documents({"usuario_id": usuario_id, "estado": "activo"})
        
        if prestamos_activos > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar el usuario porque tiene {prestamos_activos} préstamo(s) activo(s)"
            )
        
        # Eliminar el usuario
        await db.usuarios.delete_one({"_id": object_id})
        # Eliminar préstamos y reseñas asociadas
        await db.prestamos.delete_many({"usuario_id": usuario_id})
        await db.reseñas.delete_many({"usuario_id": usuario_id})
        
        logger.info(f"Usuario eliminado: '{usuario_existente['nombre']}' ({usuario_existente['email']}) (ID: {usuario_id})")
        
        return {
            "mensaje": "Usuario eliminado exitosamente",
            "usuario_eliminado": {
                "id": usuario_id,
                "nombre": usuario_existente["nombre"],
                "email": usuario_existente["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {e}")

# =============================================================================
# ENDPOINTS PRÉSTAMOS
# =============================================================================

# CREATE - Crear préstamo
@app.post("/prestamos/", response_model=PrestamoResponse, tags=["Préstamos"])
async def crear_prestamo(prestamo: Prestamo):
    try:
        # Validar que el libro existe
        libro_object_id = str_to_objectid(prestamo.libro_id)
        libro = await db.libros.find_one({"_id": libro_object_id})
        if not libro:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Validar que el usuario existe
        usuario_object_id = str_to_objectid(prestamo.usuario_id)
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que el usuario esté activo
        if not usuario.get("activo", True):
            raise HTTPException(status_code=400, detail="El usuario está inactivo y no puede realizar préstamos")
        
        # Verificar que el libro no esté ya prestado
        prestamo_activo = await db.prestamos.find_one({"libro_id": prestamo.libro_id, "estado": "activo"})
        if prestamo_activo:
            raise HTTPException(status_code=400, detail="El libro ya está prestado")
        
        # Verificar que el usuario no tenga más de 3 préstamos activos
        prestamos_usuario = await db.prestamos.count_documents({
            "usuario_id": prestamo.usuario_id, 
            "estado": "activo"
        })
        if prestamos_usuario >= 3:
            raise HTTPException(status_code=400, detail="El usuario ya tiene el máximo de 3 préstamos activos")
        
        # Verificar que el usuario no tenga préstamos vencidos
        prestamos_vencidos = await db.prestamos.count_documents({
            "usuario_id": prestamo.usuario_id,
            "estado": "activo",
            "fecha_devolucion_esperada": {"$lt": date.today().isoformat()}
        })
        if prestamos_vencidos > 0:
            raise HTTPException(status_code=400, detail="El usuario tiene préstamos vencidos y no puede realizar nuevos préstamos")
        
        # Validar fecha de devolución
        try:
            fecha_devolucion = datetime.strptime(prestamo.fecha_devolucion_esperada, "%Y-%m-%d").date()
            if fecha_devolucion <= date.today():
                raise HTTPException(status_code=400, detail="La fecha de devolución debe ser futura")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
        
        prestamo_doc = {
            "libro_id": prestamo.libro_id,
            "usuario_id": prestamo.usuario_id,
            "fecha_prestamo": datetime.now(),
            "fecha_devolucion_esperada": prestamo.fecha_devolucion_esperada,
            "fecha_devolucion_real": None,
            "estado": "activo"
        }
        
        result = await db.prestamos.insert_one(prestamo_doc)
        
        # Obtener el préstamo creado con información relacionada
        prestamo_creado = await db.prestamos.find_one({"_id": result.inserted_id})
        
        logger.info(f"Préstamo creado: Libro '{libro['titulo']}' para usuario '{usuario['nombre']}'")
        
        prestamo_creado["_id"] = str(prestamo_creado["_id"])
        prestamo_creado["fecha_prestamo"] = str(prestamo_creado["fecha_prestamo"])
        prestamo_creado["libro_titulo"] = libro["titulo"]
        prestamo_creado["usuario_nombre"] = usuario["nombre"]
        
        return PrestamoResponse(**prestamo_creado)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear préstamo: {e}")

# READ - Obtener préstamos con paginación
@app.get("/prestamos/", response_model=PaginatedPrestamosResponse, tags=["Préstamos"])
async def obtener_prestamos(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Préstamos por página"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (activo, devuelto, vencido)"),
):
    try:
        # Construir filtro
        filtro = {}
        
        if estado:
            estados_validos = ['activo', 'devuelto', 'vencido']
            if estado not in estados_validos:
                raise HTTPException(status_code=400, detail=f"Estado inválido. Estados válidos: {estados_validos}")
            filtro["estado"] = estado
        
        # Contar total
        total = await db.prestamos.count_documents(filtro)
        
        # Aplicar paginación
        skip = (pagina - 1) * por_pagina
        
        cursor = db.prestamos.find(filtro).sort("fecha_prestamo", DESCENDING).skip(skip).limit(por_pagina)
        prestamos_raw = await cursor.to_list(length=por_pagina)
        
        # Obtener información relacionada y formatear fechas
        prestamos = []
        for prestamo in prestamos_raw:
            # Obtener información del libro
            libro_object_id = str_to_objectid(prestamo["libro_id"])
            libro = await db.libros.find_one({"_id": libro_object_id})
            
            # Obtener información del usuario
            usuario_object_id = str_to_objectid(prestamo["usuario_id"])
            usuario = await db.usuarios.find_one({"_id": usuario_object_id})
            
            prestamo["_id"] = str(prestamo["_id"])
            prestamo["fecha_prestamo"] = str(prestamo["fecha_prestamo"])
            prestamo["fecha_devolucion_real"] = str(prestamo["fecha_devolucion_real"]) if prestamo.get("fecha_devolucion_real") else None
            prestamo["libro_titulo"] = libro["titulo"] if libro else "Libro eliminado"
            prestamo["usuario_nombre"] = usuario["nombre"] if usuario else "Usuario eliminado"
            
            prestamos.append(PrestamoResponse(**prestamo))
        
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return PaginatedPrestamosResponse(
            prestamos=prestamos,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener préstamos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener préstamos: {e}")

# UPDATE - Marcar préstamo como devuelto
@app.put("/prestamos/{prestamo_id}/devolver", response_model=PrestamoResponse, tags=["Préstamos"])
async def devolver_prestamo(prestamo_id: str):
    try:
        object_id = str_to_objectid(prestamo_id)
        
        # Verificar que el préstamo existe y está activo
        prestamo_existente = await db.prestamos.find_one({"_id": object_id})
        if not prestamo_existente:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        
        if prestamo_existente["estado"] != "activo":
            raise HTTPException(status_code=400, detail="Solo se pueden devolver préstamos activos")
        
        # Actualizar el préstamo
        resultado = await db.prestamos.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "estado": "devuelto",
                    "fecha_devolucion_real": datetime.now().date().isoformat()
                }
            }
        )
        
        if resultado.modified_count == 0:
            raise HTTPException(status_code=500, detail="Error al devolver el préstamo")
        
        # Obtener el préstamo actualizado
        prestamo_actualizado = await db.prestamos.find_one({"_id": object_id})
        
        # Obtener información relacionada
        libro_object_id = str_to_objectid(prestamo_actualizado["libro_id"])
        libro = await db.libros.find_one({"_id": libro_object_id})
        
        usuario_object_id = str_to_objectid(prestamo_actualizado["usuario_id"])
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        
        logger.info(f"Préstamo devuelto: ID {prestamo_id}")
        
        prestamo_actualizado["_id"] = str(prestamo_actualizado["_id"])
        prestamo_actualizado["fecha_prestamo"] = str(prestamo_actualizado["fecha_prestamo"])
        prestamo_actualizado["libro_titulo"] = libro["titulo"] if libro else "Libro eliminado"
        prestamo_actualizado["usuario_nombre"] = usuario["nombre"] if usuario else "Usuario eliminado"
        
        return PrestamoResponse(**prestamo_actualizado)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al devolver préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al devolver préstamo: {e}")

# =============================================================================
# ENDPOINTS RESEÑAS
# =============================================================================

# CREATE - Crear reseña
@app.post("/reseñas/", response_model=ReseñaResponse, tags=["Reseñas"])
async def crear_reseña(reseña: Reseña):
    try:
        # Validar que el libro existe
        libro_object_id = str_to_objectid(reseña.libro_id)
        libro = await db.libros.find_one({"_id": libro_object_id})
        if not libro:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        
        # Validar que el usuario existe
        usuario_object_id = str_to_objectid(reseña.usuario_id)
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que el usuario no haya reseñado ya este libro
        reseña_existente = await db.reseñas.find_one({
            "libro_id": reseña.libro_id,
            "usuario_id": reseña.usuario_id
        })
        if reseña_existente:
            raise HTTPException(status_code=400, detail="El usuario ya ha reseñado este libro")
        
        # Verificar que el usuario esté activo
        if not usuario.get("activo", True):
            raise HTTPException(status_code=400, detail="El usuario está inactivo y no puede crear reseñas")
        
        reseña_doc = {
            "libro_id": reseña.libro_id,
            "usuario_id": reseña.usuario_id,
            "calificacion": reseña.calificacion,
            "comentario": reseña.comentario.strip() if reseña.comentario else None,
            "fecha_reseña": datetime.now()
        }
        
        result = await db.reseñas.insert_one(reseña_doc)
        reseña_creada = await db.reseñas.find_one({"_id": result.inserted_id})
        
        logger.info(f"Reseña creada: {reseña.calificacion}/5 para '{libro['titulo']}' por '{usuario['nombre']}'")
        
        reseña_creada["_id"] = str(reseña_creada["_id"])
        reseña_creada["fecha_reseña"] = str(reseña_creada["fecha_reseña"])
        reseña_creada["libro_titulo"] = libro["titulo"]
        reseña_creada["usuario_nombre"] = usuario["nombre"]
        
        return ReseñaResponse(**reseña_creada)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear reseña: {e}")

# READ - Obtener reseñas con paginación
@app.get("/reseñas/", response_model=PaginatedReseñasResponse, tags=["Reseñas"])
async def obtener_reseñas(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Reseñas por página"),
    libro_id: Optional[str] = Query(None, description="Filtrar por libro"),
):
    try:
        # Construir filtro
        filtro = {}
        
        if libro_id:
            # Validar que el libro_id es válido
            str_to_objectid(libro_id)
            filtro["libro_id"] = libro_id
        
        # Contar total
        total = await db.reseñas.count_documents(filtro)
        
        # Aplicar paginación
        skip = (pagina - 1) * por_pagina
        
        cursor = db.reseñas.find(filtro).sort("fecha_reseña", DESCENDING).skip(skip).limit(por_pagina)
        reseñas_raw = await cursor.to_list(length=por_pagina)
        
        # Obtener información relacionada y formatear fechas
        reseñas = []
        for reseña in reseñas_raw:
            # Obtener información del libro
            libro_object_id = str_to_objectid(reseña["libro_id"])
            libro = await db.libros.find_one({"_id": libro_object_id})
            
            # Obtener información del usuario
            usuario_object_id = str_to_objectid(reseña["usuario_id"])
            usuario = await db.usuarios.find_one({"_id": usuario_object_id})
            
            reseña["_id"] = str(reseña["_id"])
            reseña["fecha_reseña"] = str(reseña["fecha_reseña"])
            reseña["libro_titulo"] = libro["titulo"] if libro else "Libro eliminado"
            reseña["usuario_nombre"] = usuario["nombre"] if usuario else "Usuario eliminado"
            
            reseñas.append(ReseñaResponse(**reseña))
        
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return PaginatedReseñasResponse(
            reseñas=reseñas,
            total=total,
            pagina=pagina,
            por_pagina=por_pagina,
            total_paginas=total_paginas
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener reseñas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener reseñas: {e}")

# READ - Obtener reseña por ID
@app.get("/reseñas/{reseña_id}", response_model=ReseñaResponse, tags=["Reseñas"])
async def obtener_reseña(reseña_id: str):
    try:
        object_id = str_to_objectid(reseña_id)
        
        reseña = await db.reseñas.find_one({"_id": object_id})
        if not reseña:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        # Obtener información relacionada
        libro_object_id = str_to_objectid(reseña["libro_id"])
        libro = await db.libros.find_one({"_id": libro_object_id})
        
        usuario_object_id = str_to_objectid(reseña["usuario_id"])
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        
        reseña["_id"] = str(reseña["_id"])
        reseña["fecha_reseña"] = str(reseña["fecha_reseña"])
        reseña["libro_titulo"] = libro["titulo"] if libro else "Libro eliminado"
        reseña["usuario_nombre"] = usuario["nombre"] if usuario else "Usuario eliminado"
        
        return ReseñaResponse(**reseña)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener reseña: {e}")

# UPDATE - Editar reseña por ID
@app.put("/reseñas/{reseña_id}", response_model=ReseñaResponse, tags=["Reseñas"])
async def editar_reseña(reseña_id: str, reseña_actualizada: ReseñaUpdate):
    try:
        object_id = str_to_objectid(reseña_id)
        
        # Verificar que la reseña existe
        reseña_existente = await db.reseñas.find_one({"_id": object_id})
        if not reseña_existente:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        # Construir actualización
        actualizacion = {}
        
        if reseña_actualizada.calificacion is not None:
            actualizacion["calificacion"] = reseña_actualizada.calificacion
        
        if reseña_actualizada.comentario is not None:
            actualizacion["comentario"] = reseña_actualizada.comentario
        
        if not actualizacion:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos válidos para actualizar")
        
        # Ejecutar actualización
        resultado = await db.reseñas.update_one(
            {"_id": object_id},
            {"$set": actualizacion}
        )
        
        if resultado.matched_count == 0:
            raise HTTPException(status_code=404, detail="Reseña no encontrada para actualizar")
        
        # Obtener la reseña actualizada
        reseña_actualizada_result = await db.reseñas.find_one({"_id": object_id})
        
        # Obtener información relacionada
        libro_object_id = str_to_objectid(reseña_actualizada_result["libro_id"])
        libro = await db.libros.find_one({"_id": libro_object_id})
        
        usuario_object_id = str_to_objectid(reseña_actualizada_result["usuario_id"])
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        
        logger.info(f"Reseña actualizada exitosamente: ID {reseña_id}")
        
        reseña_actualizada_result["_id"] = str(reseña_actualizada_result["_id"])
        reseña_actualizada_result["fecha_reseña"] = str(reseña_actualizada_result["fecha_reseña"])
        reseña_actualizada_result["libro_titulo"] = libro["titulo"] if libro else "Libro eliminado"
        reseña_actualizada_result["usuario_nombre"] = usuario["nombre"] if usuario else "Usuario eliminado"
        
        return ReseñaResponse(**reseña_actualizada_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar reseña: {e}")

# DELETE - Eliminar reseña por ID
@app.delete("/reseñas/{reseña_id}", tags=["Reseñas"])
async def eliminar_reseña(reseña_id: str):
    try:
        object_id = str_to_objectid(reseña_id)
        
        # Verificar que la reseña existe
        reseña_existente = await db.reseñas.find_one({"_id": object_id})
        if not reseña_existente:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        
        # Obtener información para el log
        libro_object_id = str_to_objectid(reseña_existente["libro_id"])
        libro = await db.libros.find_one({"_id": libro_object_id})
        
        usuario_object_id = str_to_objectid(reseña_existente["usuario_id"])
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        
        # Eliminar la reseña
        await db.reseñas.delete_one({"_id": object_id})
        
        logger.info(f"Reseña eliminada: ID {reseña_id} - {reseña_existente['calificacion']}/5")
        
        return {
            "mensaje": "Reseña eliminada exitosamente",
            "reseña_eliminada": {
                "id": reseña_id,
                "libro_titulo": libro["titulo"] if libro else "Libro eliminado",
                "usuario_nombre": usuario["nombre"] if usuario else "Usuario eliminado",
                "calificacion": reseña_existente["calificacion"],
                "comentario": reseña_existente.get("comentario", "Sin comentario")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar reseña: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar reseña: {e}")

# READ - Obtener préstamo por ID
@app.get("/prestamos/{prestamo_id}", response_model=PrestamoResponse, tags=["Préstamos"])
async def obtener_prestamo(prestamo_id: str):
    try:
        object_id = str_to_objectid(prestamo_id)
        
        prestamo = await db.prestamos.find_one({"_id": object_id})
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        
        # Obtener información relacionada
        libro_object_id = str_to_objectid(prestamo["libro_id"])
        libro = await db.libros.find_one({"_id": libro_object_id})
        
        usuario_object_id = str_to_objectid(prestamo["usuario_id"])
        usuario = await db.usuarios.find_one({"_id": usuario_object_id})
        
        prestamo["_id"] = str(prestamo["_id"])
        prestamo["fecha_prestamo"] = str(prestamo["fecha_prestamo"])
        prestamo["fecha_devolucion_real"] = str(prestamo["fecha_devolucion_real"]) if prestamo.get("fecha_devolucion_real") else None
        prestamo["libro_titulo"] = libro["titulo"] if libro else "Libro eliminado"
        prestamo["usuario_nombre"] = usuario["nombre"] if usuario else "Usuario eliminado"
        
        return PrestamoResponse(**prestamo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener préstamo: {e}")

# ESTADÍSTICAS COMPLETAS
@app.get("/estadisticas/", response_model=Estadisticas, tags=["Estadísticas"])
async def obtener_estadisticas():
    try:
        # Total de libros
        total_libros = await db.libros.count_documents({})
        
        # Total de usuarios
        total_usuarios = await db.usuarios.count_documents({})
        
        # Total de préstamos
        total_prestamos = await db.prestamos.count_documents({})
        
        # Total de reseñas
        total_reseñas = await db.reseñas.count_documents({})
        
        # Libros por género
        pipeline_genero = [
            {"$match": {"genero": {"$ne": None}}},
            {"$group": {"_id": "$genero", "cantidad": {"$sum": 1}}},
            {"$sort": {"cantidad": -1}}
        ]
        libros_por_genero_cursor = db.libros.aggregate(pipeline_genero)
        libros_por_genero = {doc["_id"]: doc["cantidad"] async for doc in libros_por_genero_cursor}
        
        # Libros por año (últimos 10 años)
        año_actual = datetime.now().year
        pipeline_año = [
            {"$match": {"año": {"$gte": año_actual - 10}}},
            {"$group": {"_id": "$año", "cantidad": {"$sum": 1}}},
            {"$sort": {"_id": -1}}
        ]
        libros_por_año_cursor = db.libros.aggregate(pipeline_año)
        libros_por_año = {str(doc["_id"]): doc["cantidad"] async for doc in libros_por_año_cursor}
        
        # Usuarios por tipo
        pipeline_tipo = [
            {"$group": {"_id": "$tipo_usuario", "cantidad": {"$sum": 1}}},
            {"$sort": {"cantidad": -1}}
        ]
        usuarios_por_tipo_cursor = db.usuarios.aggregate(pipeline_tipo)
        usuarios_por_tipo = {doc["_id"]: doc["cantidad"] async for doc in usuarios_por_tipo_cursor}
        
        # Préstamos activos
        prestamos_activos = await db.prestamos.count_documents({"estado": "activo"})
        
        # Préstamos vencidos (activos pero con fecha vencida)
        fecha_actual = datetime.now().date()
        prestamos_vencidos = await db.prestamos.count_documents({
            "estado": "activo", 
            "fecha_devolucion_esperada": {"$lt": fecha_actual.isoformat()}
        })
        
        # Promedio de calificaciones
        pipeline_promedio = [
            {"$group": {"_id": None, "promedio": {"$avg": "$calificacion"}}}
        ]
        promedio_cursor = db.reseñas.aggregate(pipeline_promedio)
        promedio_result = None
        async for doc in promedio_cursor:
            promedio_result = doc["promedio"]
            break
        promedio_calificaciones = float(promedio_result) if promedio_result else 0.0
        
        # Autores únicos
        autores_unicos = len(await db.libros.distinct("autor"))
        
        # Géneros únicos
        generos_unicos = len(await db.libros.distinct("genero", {"genero": {"$ne": None}}))
        
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
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)