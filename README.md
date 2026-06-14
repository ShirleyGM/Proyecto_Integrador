# Reconocimiento Automático de Placas Vehiculares (ALPR)

Sistema de detección y reconocimiento en tiempo real de placas vehiculares usando visión computacional, OCR y almacenamiento en MongoDB.

## Estructura del Proyecto

- **main.py**: Script principal del sistema ALPR
- **plate_reader.py**: Detección y OCR de placas
- **requirements.txt**: Dependencias Python
- **docker-compose.yml**: Servicios MongoDB + Mongo Express
- **Dockerfile**: Imagen Docker (referencia, no se usa en Opción 1)

## Requisitos

- Python 3.10+
- Tesseract OCR
- Docker Desktop y Docker Compose
- Una cámara conectada

## Instalación

### 1. Instala Tesseract OCR

**Windows:**
- Descarga: https://github.com/UB-Mannheim/tesseract/wiki
- Instala en `C:\Program Files\Tesseract-OCR`
- O especifica la ruta en la variable `TESSERACT_CMD`

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 2. Configura el entorno Python

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# o
source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 3. Inicia MongoDB en Docker

```bash
docker-compose up -d
```

Esto inicia:
- **MongoDB**: Puerto 27017 (credenciales: `mongo_user` / `mongo_pass`)
- **Mongo Express**: Puerto 8081 (UI para ver datos)

## Uso

### Ejecutar el sistema ALPR

```bash
python main.py
```

**Opciones:**
```bash
# Modo con ventana (predeterminado en host)
python main.py

# Procesar una imagen específica
IMAGE_SOURCE=ruta/a/imagen.jpg python main.py

# Especificar fuente de cámara (si tienes múltiples)
VIDEO_SOURCE=1 python main.py

# Modo headless (sin ventana)
HEADLESS=1 python main.py
```

**Teclas:**
- Presiona `q` para salir (si no está en modo headless)

## Base de Datos - MongoDB

### Colección: `placas`

Cada detección se almacena como:

```json
{
  "_id": ObjectId("..."),
  "numero_placa": "ABC1234",
  "fecha_hora": "2026-05-14T10:30:45.123Z",
  "coordenadas_x": 150,
  "coordenadas_y": 200,
  "ancho": 120,
  "alto": 40,
  "confianza": 0.95,
  "imagen_path": "captures/ABC1234_20260514_103045.jpg"
}
```

### Ver los datos

Accede a **Mongo Express** en: http://localhost:8081

- Usuario: `admin`
- Contraseña: `mongo_pass` (por defecto en docker-compose)
- Base de datos: `alpr_db`

## Configuración

### Variables de Entorno

```bash
# MongoDB
MONGO_URI=mongodb://mongo_user:mongo_pass@localhost:27017/alpr_db

# Tesseract (si no está en PATH)
TESSERACT_CMD=/ruta/a/tesseract

# Interfaz
HEADLESS=0  # 0 = mostrar ventana, 1 = sin ventana

# Cámara/Video
VIDEO_SOURCE=0  # 0 = cámara predeterminada, "ruta/archivo.mp4" = video file
IMAGE_SOURCE=ruta/imagen.jpg  # Procesar una imagen
```

## Solución de Problemas

### "No se encontró Tesseract"
```bash
# Windows: Verifica la instalación o establece TESSERACT_CMD
TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe" python main.py

# Linux/macOS: Instala tesseract-ocr
```

### "MongoDB no disponible"
```bash
# Verifica que Docker esté corriendo
docker ps

# Reinicia MongoDB
docker-compose restart mongo
```

### La cámara no funciona
```bash
# Prueba con VIDEO_SOURCE=0 (predeterminado)
# Si no funciona, intenta VIDEO_SOURCE=1 (segunda cámara)
VIDEO_SOURCE=1 python main.py
```

### Permisos de cámara (macOS)
```bash
# Abre Configuración > Privacidad > Cámara
# Permite que Terminal acceda a la cámara
```

## Módulos

### plate_reader.py

Clase `PlateReader`:
- `detect_plates(image)`: Detecta regiones de placas
- `recognize_text(plate_roi)`: OCR del texto
- `process_frame(frame)`: Procesa un frame completo

### main.py

Clase `MongoDBManager`:
- `connect()`: Conecta a MongoDB
- `insert_plate()`: Guarda una detección
- `close()`: Cierra la conexión

## Notas

- Las capturas se guardan en carpeta `captures/` con timestamp
- Si MongoDB no está disponible, el sistema guarda solo localmente
- Presiona `q` para salir (modo no-headless)
- El clasificador de placas se optimiza mejor con imágenes de buena calidad
