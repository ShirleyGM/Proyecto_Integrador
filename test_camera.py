import os
import cv2
import time
from datetime import datetime
from plate_reader import PlateReader

def save_capture(frame, plate_text):
    os.makedirs('captures', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"captures/capture_{plate_text}_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"  📸 Captura guardada: {filename}")
    return filename


def detect_plate_in_image(filename, plate_reader):
    image = cv2.imread(filename)
    if image is None:
        print(f"  ❌ No se pudo leer la imagen guardada: {filename}")
        return []

    _, readings = plate_reader.process_frame(image, draw_rectangles=False)
    if readings:
        print(f"  🔎 Detecciones en imagen guardada: {filename}")
        for reading in readings:
            print(f"    • Placa: {reading.get('texto')} | Coords: {reading.get('coords')}")
    else:
        print(f"  ⚠️  No se detectaron placas en la imagen guardada: {filename}")
    return readings


def main():
    """
    Prueba simple: conectarse a la cámara y leer placas.
    Muestra lo que ve la cámara en pantalla.
    """
    
    print("=== PRUEBA DE CÁMARA Y LECTURA DE PLACAS ===\n")
    
    # Inicializar el lector de placas
    print("Inicializando lector de placas...")
    tesseract_cmd = os.getenv('TESSERACT_CMD', None)
    plate_reader = PlateReader(tesseract_cmd=tesseract_cmd)
    print(f"Tesseract disponible: {plate_reader.tesseract_available}\n")
    
    # Conectar a la cámara
    print("Intentando conectar a la cámara (índice 0)...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ ERROR: No se pudo abrir la cámara.")
        print("Asegúrate de que:")
        print("  - La cámara está conectada")
        print("  - Docker tiene permisos para acceder a /dev/video0")
        print("  - En Windows, la cámara no está siendo usada por otra aplicación")
        return
    
    print("✅ Cámara conectada exitosamente!\n")
    
    # Configurar propiedades de la cámara
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Verificar si estamos en Docker o en local
    in_docker = os.path.exists('/.dockerenv')
    headless = os.getenv('HEADLESS', '0').lower() in ('1', 'true', 'yes')
    
    if in_docker:
        print("⚠️  Ejecutándose en Docker (sin GUI)")
        print("   Guardando video en 'camera_output.avi'...\n")
        # Inicializar escritor de video
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter('camera_output.avi', fourcc, 30.0, (640, 480))
        show_video = False
    else:
        print("✅ Modo local detectado. Mostrando ventana en pantalla.\n")
        print("Presiona 'q' para salir.\n")
        show_video = True
        out = None
    
    frame_count = 0
    plates_detected = 0
    plates_recognized = 0
    saved_captures = set()
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Error al leer frame de la cámara")
                break
            
            frame_count += 1
            
            # Procesar frame
            processed_frame, readings = plate_reader.process_frame(frame, draw_rectangles=True)
            
            # Contar resultados y capturar placas válidas de 7 caracteres
            if readings:
                plates_detected += len(readings)
                for reading in readings:
                    text = reading.get('texto')
                    if text:
                        plates_recognized += 1
                        print(f"  → Placa encontrada: {text}")
                        if len(text) == 7 and text.isalnum():
                            if text not in saved_captures:
                                capture_file = save_capture(processed_frame, text)
                                saved_captures.add(text)
                                detect_plate_in_image(capture_file, plate_reader)
                            else:
                                print(f"  🔁 Placa {text} ya capturada anteriormente")
            
            # Mostrar estadísticas en el frame
            stats_text = f"Frames: {frame_count} | Placas detectadas: {plates_detected} | Reconocidas: {plates_recognized}"
            cv2.putText(processed_frame, stats_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mostrar en pantalla si no estamos en Docker
            if show_video and not headless:
                cv2.imshow('ALPR - Prueba de Cámara', processed_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n✅ Prueba finalizada por el usuario.")
                    break
            
            # Guardar video si estamos en Docker
            if out is not None:
                out.write(processed_frame)
                if frame_count % 30 == 0:
                    print(f"  Frames guardados: {frame_count}")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrupción del usuario")
    
    finally:
        cap.release()
        if out is not None:
            out.release()
            print(f"✅ Video guardado en: camera_output.avi")
        
        if show_video:
            cv2.destroyAllWindows()
        
        print(f"\n=== RESUMEN ===")
        print(f"Frames procesados: {frame_count}")
        print(f"Placas detectadas: {plates_detected}")
        print(f"Placas reconocidas: {plates_recognized}")

if __name__ == "__main__":
    main()
