# 📚 API Biblioteca Mejorada

Una API completa para gestión de biblioteca construida con FastAPI y MySQL, con funcionalidades avanzadas de búsqueda, filtros, paginación y estadísticas.

## 🚀 Características

- **CRUD completo** de libros
- **Búsqueda avanzada** por título, autor, género y descripción
- **Filtros múltiples** por género, año mínimo/máximo
- **Paginación** configurable
- **Ordenamiento** por diferentes campos
- **Estadísticas** de la biblioteca
- **Validaciones** robustas con Pydantic
- **Logging** para monitoreo
- **Documentación automática** con Swagger

## 🛠️ Instalación

1. **Clonar el repositorio:**
```bash
git clone <tu-repositorio>
cd simple_api
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos:**
   - Asegúrate de que tu base de datos MySQL esté configurada
   - La tabla se creará automáticamente al iniciar la API

4. **Ejecutar la API:**
```bash
python main.py
```

La API estará disponible en: `http://127.0.0.1:8000`
Documentación Swagger: `http://127.0.0.1:8000/docs`

## 📖 Endpoints Disponibles

### 🏠 Información General
- `GET /` - Información de la API y endpoints disponibles

### 📚 CRUD de Libros
- `POST /libros/` - Crear un nuevo libro
- `GET /libros/` - Obtener libros con paginación y filtros
- `GET /libros/{id}` - Obtener libro por ID
- `PATCH /libros/{id}` - Actualizar libro (parcial)
- `DELETE /libros/{id}` - Eliminar libro

### 🔍 Búsqueda
- `GET /libros/buscar/` - Búsqueda avanzada por término

### 📊 Estadísticas
- `GET /libros/estadisticas/` - Estadísticas de la biblioteca

### 🛠️ Utilidades
- `GET /libros/generos/` - Obtener lista de géneros únicos
- `GET /libros/autores/` - Obtener lista de autores únicos

## 📝 Ejemplos de Uso

### Crear un libro
```bash
curl -X POST "http://127.0.0.1:8000/libros/" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "El Señor de los Anillos",
    "autor": "J.R.R. Tolkien",
    "año": 1954,
    "genero": "Fantasía",
    "isbn": "9788445071405",
    "descripcion": "Una épica historia de fantasía"
  }'
```

### Obtener libros con filtros
```bash
curl "http://127.0.0.1:8000/libros/?pagina=1&por_pagina=10&genero=Fantasía&año_min=1950&ordenar_por=titulo&orden=asc"
```

### Buscar libros
```bash
curl "http://127.0.0.1:8000/libros/buscar/?q=tolkien&campo=autor"
```

### Obtener estadísticas
```bash
curl "http://127.0.0.1:8000/libros/estadisticas/"
```

## 🔧 Parámetros de Consulta

### GET /libros/
- `pagina` (int): Número de página (default: 1)
- `por_pagina` (int): Libros por página (default: 10, max: 100)
- `ordenar_por` (str): Campo para ordenar (id, titulo, autor, año, genero)
- `orden` (str): Orden ascendente o descendente (asc/desc)
- `genero` (str): Filtrar por género
- `año_min` (int): Año mínimo de publicación
- `año_max` (int): Año máximo de publicación

### GET /libros/buscar/
- `q` (str): Término de búsqueda (requerido)
- `campo` (str): Campo a buscar (titulo, autor, genero, descripcion)

## 📊 Modelo de Datos

### Libro
```json
{
  "titulo": "string (1-200 caracteres)",
  "autor": "string (1-100 caracteres)",
  "año": "integer (1000-actual)",
  "genero": "string (opcional, max 50 caracteres)",
  "isbn": "string (opcional, max 13 caracteres)",
  "descripcion": "string (opcional, max 500 caracteres)"
}
```

### Respuesta Paginada
```json
{
  "libros": [...],
  "total": "integer",
  "pagina": "integer",
  "por_pagina": "integer",
  "total_paginas": "integer"
}
```

### Estadísticas
```json
{
  "total_libros": "integer",
  "libros_por_genero": "object",
  "libros_por_año": "object",
  "autores_unicos": "integer",
  "generos_unicos": "integer"
}
```

## 🗄️ Base de Datos

La API utiliza MySQL con la siguiente estructura de tabla:

```sql
CREATE TABLE libros (
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
);
```

## 🔍 Funcionalidades Avanzadas

### Búsqueda Inteligente
- Búsqueda por similitud en títulos, autores, géneros y descripciones
- Resultados ordenados por relevancia

### Filtros Combinados
- Múltiples filtros aplicables simultáneamente
- Rango de años personalizable
- Filtro por género específico

### Paginación Eficiente
- Control total sobre el número de resultados por página
- Información de navegación incluida en la respuesta
- Límites de seguridad para evitar sobrecarga

### Estadísticas en Tiempo Real
- Conteo total de libros
- Distribución por género
- Distribución por año (últimos 10 años)
- Conteo de autores y géneros únicos

## 🛡️ Validaciones

- **Títulos**: 1-200 caracteres
- **Autores**: 1-100 caracteres
- **Años**: Entre 1000 y el año actual
- **Géneros**: Máximo 50 caracteres
- **ISBN**: Máximo 13 caracteres
- **Descripciones**: Máximo 500 caracteres

## 📈 Logging

La API incluye logging detallado para:
- Creación de libros
- Actualizaciones
- Eliminaciones
- Búsquedas realizadas
- Errores de base de datos

## 🚀 Próximas Mejoras

- [ ] Autenticación JWT
- [ ] Sistema de préstamos
- [ ] Rate limiting
- [ ] Caché con Redis
- [ ] Exportación a CSV/PDF
- [ ] API de recomendaciones

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.