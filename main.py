from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import mysql.connector
from datetime import datetime, date, timedelta
import logging
import random

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

# Función para conectar a la base de datos
def get_connection():
    try:
        return mysql.connector.connect(**DATABASE_CONFIG)
    except mysql.connector.Error as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error de conexión: {e}")

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
    id: int
    fecha_creacion: Optional[str] = None

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
    id: int
    fecha_registro: Optional[str] = None
    activo: bool = True

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=15)
    direccion: Optional[str] = Field(None, max_length=300)
    tipo_usuario: Optional[str] = None
    activo: Optional[bool] = None

# Modelos Pydantic - PRÉSTAMOS
class Prestamo(BaseModel):
    libro_id: int = Field(..., description="ID del libro a prestar")
    usuario_id: int = Field(..., description="ID del usuario")
    fecha_devolucion_esperada: str = Field(..., description="Fecha esperada de devolución (YYYY-MM-DD)")

class PrestamoResponse(BaseModel):
    id: int
    libro_id: int
    usuario_id: int
    fecha_prestamo: str
    fecha_devolucion_esperada: str
    fecha_devolucion_real: Optional[str] = None
    estado: str
    libro_titulo: Optional[str] = None
    usuario_nombre: Optional[str] = None

class PrestamoUpdate(BaseModel):
    fecha_devolucion_esperada: Optional[str] = None
    estado: Optional[str] = None

# Modelos Pydantic - RESEÑAS
class Reseña(BaseModel):
    libro_id: int = Field(..., description="ID del libro a reseñar")
    usuario_id: int = Field(..., description="ID del usuario que hace la reseña")
    calificacion: int = Field(..., ge=1, le=5, description="Calificación del 1 al 5")
    comentario: Optional[str] = Field(None, max_length=1000, description="Comentario sobre el libro")

class ReseñaResponse(Reseña):
    id: int
    fecha_reseña: str
    libro_titulo: Optional[str] = None
    usuario_nombre: Optional[str] = None

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

# Crear todas las tablas si no existen
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear tabla libros
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
    
    # Crear tabla usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            telefono VARCHAR(15),
            direccion VARCHAR(300),
            tipo_usuario ENUM('estudiante', 'profesor', 'administrador') DEFAULT 'estudiante',
            activo BOOLEAN DEFAULT TRUE,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_tipo (tipo_usuario),
            INDEX idx_activo (activo)
        )
    """)
    
    # Crear tabla préstamos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            libro_id INT NOT NULL,
            usuario_id INT NOT NULL,
            fecha_prestamo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_devolucion_esperada DATE NOT NULL,
            fecha_devolucion_real DATE NULL,
            estado ENUM('activo', 'devuelto', 'vencido') DEFAULT 'activo',
            FOREIGN KEY (libro_id) REFERENCES libros(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            INDEX idx_libro (libro_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_estado (estado),
            INDEX idx_fecha_devolucion (fecha_devolucion_esperada)
        )
    """)
    
    # Crear tabla reseñas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reseñas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            libro_id INT NOT NULL,
            usuario_id INT NOT NULL,
            calificacion INT NOT NULL CHECK (calificacion >= 1 AND calificacion <= 5),
            comentario TEXT,
            fecha_reseña TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (libro_id) REFERENCES libros(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            UNIQUE KEY unique_reseña (libro_id, usuario_id),
            INDEX idx_libro (libro_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_calificacion (calificacion)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# Función para poblar la base de datos con datos de prueba
def poblar_datos_iniciales():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM libros")
        if cursor.fetchone()[0] > 0:
            logger.info("La base de datos ya contiene datos, omitiendo población inicial")
            cursor.close()
            conn.close()
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
        
        # Insertar libros
        for libro in libros_data:
            cursor.execute("""
                INSERT INTO libros (titulo, autor, año, genero, isbn, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, libro)
        
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
        
        # Insertar usuarios
        for usuario in usuarios_data:
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, telefono, direccion, tipo_usuario)
                VALUES (%s, %s, %s, %s, %s)
            """, usuario)
        
        conn.commit()
        
        # Obtener IDs insertados para crear relaciones
        cursor.execute("SELECT id FROM libros")
        libro_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM usuarios")
        usuario_ids = [row[0] for row in cursor.fetchall()]
        
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
            
            cursor.execute("""
                INSERT INTO prestamos (libro_id, usuario_id, fecha_prestamo, fecha_devolucion_esperada, fecha_devolucion_real, estado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (libro_id, usuario_id, fecha_prestamo, fecha_devolucion_esperada, fecha_devolucion_real, estado))
            
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
            
            cursor.execute("""
                INSERT INTO reseñas (libro_id, usuario_id, calificacion, comentario, fecha_reseña)
                VALUES (%s, %s, %s, %s, %s)
            """, (libro_id, usuario_id, calificacion, comentario, fecha_reseña))
            
            reseñas_creadas.add((libro_id, usuario_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Base de datos poblada exitosamente con:")
        logger.info(f"   📚 {len(libros_data)} libros")
        logger.info(f"   👥 {len(usuarios_data)} usuarios") 
        logger.info(f"   📋 20 préstamos")
        logger.info(f"   ⭐ 25 reseñas")
        
    except Exception as e:
        logger.error(f"Error al poblar datos iniciales: {e}")
        try:
            cursor.close()
            conn.close()
        except:
            pass

# Función de lifespan para inicializar las tablas
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    poblar_datos_iniciales()
    logger.info("🚀 API iniciada - Tablas creadas y datos poblados automáticamente")
    yield
    # Shutdown (si fuera necesario)
    pass

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
        "mensaje": "API de Biblioteca Mejorada - FastAPI con MySQL",
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
@app.get("/libros/", response_model=PaginatedResponse, tags=["Libros"])
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