# Reconocimiento Automático de Placas Vehiculares (ALPR) con PostgreSQL

Este proyecto implementa un sistema de reconocimiento automático de placas vehiculares usando cámara en tiempo real y almacenamiento en base de datos PostgreSQL.

## Estructura del Proyecto

- **main.py**: Script principal que ejecuta el sistema ALPR
- **plate_reader.py**: Módulo para detección y reconocimiento de placas
- **database.py**: Módulo para gestionar la conexión y operaciones con PostgreSQL
- **requirements.txt**: Dependencias del proyecto

## Requisitos

- Python 3.x
- Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki)
- PostgreSQL 12+
- Una cámara conectada

## Instalación

1. Crea un entorno virtual:
   ```
   python -m venv .venv
   ```

2. Activa el entorno virtual:
   ```
   .venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Asegúrate de que Tesseract esté instalado en `C:\Program Files\Tesseract-OCR\` (ajusta la ruta en `main.py` si es necesario).

## Configuración de Base de Datos

### 1. Instala PostgreSQL
Descarga desde https://www.postgresql.org/download/windows/

### 2. Crea la base de datos
```sql
CREATE DATABASE placas_db;
```

### 3. Actualiza las credenciales en main.py
En `main.py`, modifica los parámetros de conexión:
```python
db = DatabaseManager(
    host='localhost',
    database='placas_db',
    user='tu_usuario',
    password='tu_contraseña',
    port=5432
)
```

## Uso

Ejecuta el script:
```
python main.py
```

### Funcionalidades

- **Detección en tiempo real**: Detecta placas vehiculares usando cámara
- **Reconocimiento OCR**: Extrae el texto de las placas
- **Almacenamiento automático**: Guarda cada placa detectada en PostgreSQL con:
  - Número de placa
  - Fecha y hora
  - Coordenadas en la imagen
  - Dimensiones de la región detectada

### Salir de la aplicación
Presiona 'q' para cerrar la ventana y terminar el programa.

## Módulos

### plate_reader.py
Clase `PlateReader` con métodos:
- `detect_plates(image)`: Detecta placas en una imagen
- `recognize_text(plate_roi)`: Realiza OCR en una región
- `process_frame(frame)`: Procesa un frame completo y retorna las lecturas

### database.py
Clase `DatabaseManager` con métodos:
- `connect()`: Conecta a PostgreSQL
- `disconnect()`: Cierra la conexión
- `create_table()`: Crea la tabla de placas
- `insert_plate(numero_placa, coords)`: Guarda una placa
- `get_all_plates()`: Obtiene todas las placas
- `get_plates_by_date()`: Consulta por rango de fechas

## Estructura de la Base de Datos

```sql
CREATE TABLE placas (
    id SERIAL PRIMARY KEY,
    numero_placa VARCHAR(20) NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    coordenadas_x INTEGER,
    coordenadas_y INTEGER,
    ancho INTEGER,
    alto INTEGER,
    confianza FLOAT DEFAULT 0.0
);
```

## Notas

- El clasificador para placas rusas puede necesitar ajuste para otros formatos
- Asegúrate de tener suficientes permisos en PostgreSQL
- Tesseract debe estar en el PATH o especificar la ruta correcta