import os
import re
import time
import cv2
import datetime
import threading
from plate_reader import PlateReader
from vehicle_lookup import VehicleLookup
from pymongo import MongoClient

class MongoDBManager:
    def __init__(self, mongo_uri="mongodb://mongo_user:mongo_pass@localhost:27017/alpr_db"):
        self.mongo_uri = mongo_uri
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=3000)
            self.client.admin.command('ping')
            self.db = self.client['alpr_db']
            self.collection = self.db['placas']
            print("✓ Conectado a MongoDB", flush=True)
        except Exception as e:
            print(f"⚠ MongoDB no disponible ({type(e).__name__}). Guardando solo localmente.", flush=True)
            self.client = None

    def insert_plate(self, numero_placa, coords_x, coords_y, ancho, alto, confianza, imagen_path):
        if not self.client:
            return None
        try:
            record = {
                "numero_placa": numero_placa,
                "fecha_hora": datetime.datetime.utcnow(),
                "coordenadas_x": coords_x,
                "coordenadas_y": coords_y,
                "ancho": ancho,
                "alto": alto,
                "confianza": confianza,
                "imagen_path": imagen_path
            }
            result = self.collection.insert_one(record)
            return result.inserted_id
        except Exception as e:
            print(f"⚠ Error al guardar en MongoDB: {e}", flush=True)
            return None

    def close(self):
        if self.client:
            self.client.close()

def save_capture(frame, plate_text, plate_coords=None):
    os.makedirs('captures', exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"captures/{plate_text}_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"  📸 Captura guardada: {filename}")
    return filename

def _print_vehicle_info(plate: str, confianza: float, vehicle: dict | None):
    sep = "-" * 40
    print(sep, flush=True)
    print(f"  PLACA DETECTADA : {plate}  (confianza: {confianza:.1%})", flush=True)
    if vehicle:
        conductor = vehicle.get("conductor", {})
        print(f"  Tipo vehículo   : {vehicle.get('tipo_vehiculo', '-')}", flush=True)
        print(f"  Tipo carga      : {vehicle.get('tipo_carga', '-')}", flush=True)
        print(f"  Conductor       : {conductor.get('nombre', '-')}", flush=True)
        print(f"  Cédula          : {conductor.get('cedula', '-')}", flush=True)
        print(f"  Teléfono        : {conductor.get('telefono', '-')}", flush=True)
    else:
        print(f"  ⚠ Vehículo no registrado en la base de datos.", flush=True)
    print(sep, flush=True)

def main():
    """
    Sistema ALPR con almacenamiento en MongoDB y captura local.
    """
    print("Inicializando lector de placas...")
    tesseract_cmd = os.getenv('TESSERACT_CMD', None)
    plate_reader = PlateReader(tesseract_cmd=tesseract_cmd)

    # Conectar a MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo_user:mongo_pass@localhost:27017/alpr_db?authSource=admin')
    db_manager = MongoDBManager(mongo_uri)
    vehicle_lookup = VehicleLookup(mongo_uri)

    # Seleccionar fuente de entrada
    image_source = os.getenv('IMAGE_SOURCE', '').strip()
    video_source = os.getenv('VIDEO_SOURCE', '0').strip()
    headless = os.getenv('HEADLESS', '0').lower() in ('1', 'true', 'yes')

    if image_source:
        print(f"Procesando imagen: {image_source}", flush=True)
        if not os.path.exists(image_source):
            print(f"No se encontró la imagen '{image_source}'.", flush=True)
            exit(1)
        image = cv2.imread(image_source)
        if image is None:
            print(f"No se pudo leer la imagen '{image_source}'.", flush=True)
            exit(1)

        processed_frame, readings = plate_reader.process_frame(image, draw_rectangles=True)
        output_path = os.getenv('OUTPUT_IMAGE', 'output.jpg')
        cv2.imwrite(output_path, processed_frame)

        if readings:
            for reading in readings:
                text = reading.get('texto')
                if text and len(text) == 7 and text.isalnum():
                    db_manager.insert_plate(text, 0, 0, 0, 0, 0.0, output_path)

        print(f"Imagen procesada. Resultado guardado en {output_path}", flush=True)
        db_manager.close()
        exit(0)

    if not video_source:
        print("No se configuró VIDEO_SOURCE.", flush=True)
        db_manager.close()
        exit(1)

    print(f"Fuente de video: {video_source}", flush=True)
    try:
        source = int(video_source)
    except ValueError:
        source = video_source

    print("Abriendo cámara...", flush=True)

    cap = None
    def open_camera():
        nonlocal cap
        # CAP_DSHOW primero en Windows (más rápido y compatible con USB)
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source)

    camera_thread = threading.Thread(target=open_camera, daemon=True)
    camera_thread.start()
    camera_thread.join(timeout=10)

    if cap is None or not cap.isOpened():
        print(f"✗ No se pudo abrir cámara '{video_source}'.", flush=True)
        print(f"  1. Verifica que la cámara esté conectada", flush=True)
        print(f"  2. Cierra otras aplicaciones usando la cámara (Teams, Zoom, etc.)", flush=True)
        print(f"  3. Prueba VIDEO_SOURCE=1 si tienes múltiples cámaras", flush=True)
        db_manager.close()
        exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("✓ Cámara abierta correctamente. Calentando...", flush=True)

    # Warmup: descartar los primeros frames hasta que la cámara produzca imagen real
    warmup_ok = False
    for _ in range(30):
        ret, _ = cap.read()
        if ret:
            warmup_ok = True
            break
        time.sleep(0.1)

    if not warmup_ok:
        print("✗ La cámara abrió pero no produce frames. Verifica que no la use otra aplicación.", flush=True)
        cap.release()
        db_manager.close()
        exit(1)

    print("✓ Cámara lista.", flush=True)

    frame_count = 0
    plates_detected = 0
    plates_recognized = 0
    saved_captures = set()
    process_every = int(os.getenv('PROCESS_EVERY', '5'))
    last_readings = []
    last_detections = {}   # plate -> {'coords': (x,y,w,h), 'vehicle': dict|None}
    consecutive_failures = 0
    MAX_FAILURES = 10

    print("Sistema ALPR iniciado.", flush=True)
    if headless:
        print("Modo headless: sin ventana de salida.", flush=True)
    else:
        print("Presiona 'q' para salir.", flush=True)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= MAX_FAILURES:
                    print("✗ Demasiados frames fallidos consecutivos. Cerrando.", flush=True)
                    break
                time.sleep(0.05)
                continue
            consecutive_failures = 0

            frame_count += 1

            is_detection_frame = (frame_count % process_every == 0)
            if is_detection_frame:
                processed_frame, last_readings = plate_reader.process_frame(frame, draw_rectangles=True)
                plates_detected += len(last_readings)

                last_detections.clear()
                for reading in last_readings:
                    text = reading.get('texto')
                    coords = reading.get('coords', (0, 0, 0, 0))
                    confianza = reading.get('confianza', 0.0)

                    if text and re.fullmatch(r'[A-Z]{3}[0-9]{4}', text):
                        plates_recognized += 1
                        vehicle = vehicle_lookup.find_by_plate(text)

                        if text not in saved_captures:
                            imagen_path = save_capture(processed_frame, text, coords)
                            x, y, w, h = coords
                            db_manager.insert_plate(text, x, y, w, h, confianza, imagen_path)
                            saved_captures.add(text)
                            _print_vehicle_info(text, confianza, vehicle)
                        else:
                            print(f"  🔁 Placa {text} ya capturada", flush=True)
            else:
                processed_frame = frame

            stats_text = f"Frames: {frame_count} | Detectadas: {plates_detected} | Reconocidas: {plates_recognized}"
            cv2.putText(processed_frame, stats_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            if not headless:
                cv2.imshow('ALPR', processed_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01)

    finally:
        cap.release()
        if not headless:
            cv2.destroyAllWindows()
        db_manager.close()

        print("\n=== RESUMEN ===")
        print(f"Frames procesados: {frame_count}")
        print(f"Placas detectadas: {plates_detected}")
        print(f"Placas reconocidas: {plates_recognized}")

if __name__ == "__main__":
    main()
