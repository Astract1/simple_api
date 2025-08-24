# API Biblioteca Simple - FastAPI + MySQL

## Problema
Sistema básico para gestionar una biblioteca con operaciones CRUD sobre libros.

## Instalación

1. **Crear entorno virtual:**
```bash
pip install virtualenv
virtualenv venv
venv\Scripts\activate
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos:**
Edita `main.py` líneas 8-13 con tus datos de Railway MySQL:
```python
DATABASE_CONFIG = {
    "host": "tu-host-railway.com",
    "port": 6543,
    "user": "root", 
    "password": "tu_password",
    "database": "railway"
}
```

4. **Ejecutar:**
```bash
python main.py
```

## Endpoints

- `GET /` - Inicio
- `POST /libros/` - Crear libro
- `GET /libros/` - Listar libros
- `GET /libros/{id}` - Obtener libro
- `PUT /libros/{id}` - Actualizar libro  
- `DELETE /libros/{id}` - Eliminar libro

## Documentación
Ve a: http://localhost:8000/docs

## Estructura MySQL
```sql
CREATE TABLE libros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    autor VARCHAR(100) NOT NULL,
    año INT NOT NULL,
    genero VARCHAR(50)
);
```

## Ejemplo de uso
```bash
# Crear libro
curl -X POST "http://localhost:8000/libros/" \
  -H "Content-Type: application/json" \
  -d '{"titulo": "El Quijote", "autor": "Cervantes", "año": 1605, "genero": "Novela"}'
```