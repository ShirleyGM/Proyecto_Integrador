import os
import time
import cv2
from plate_reader import PlateReader

def main():
    """
    Función principal que ejecuta el sistema ALPR sin conexión a base de datos.
    """
    
    # Inicializar el lector de placas
    print("Inicializando lector de placas...")
    tesseract_cmd = os.getenv('TESSERACT_CMD', None)  # None permitirá búsqueda automática
    plate_reader = PlateReader(tesseract_cmd=tesseract_cmd)
    
    # Seleccionar fuente de entrada
    image_source = os.getenv('IMAGE_SOURCE', '').strip()
    video_source = os.getenv('VIDEO_SOURCE', '0').strip()
    headless = os.getenv('HEADLESS', '1').lower() in ('1', 'true', 'yes')
    if image_source:
        print(f"Procesando imagen: {image_source}", flush=True)
        if not os.path.exists(image_source):
            print(f"No se encontró la imagen '{image_source}'.", flush=True)
            exit(1)
        image = cv2.imread(image_source)
        if image is None:
            print(f"No se pudo leer la imagen '{image_source}'.", flush=True)
            exit(1)

        processed_frame, _ = plate_reader.process_frame(image, draw_rectangles=True)
        output_path = os.getenv('OUTPUT_IMAGE', 'output.jpg')
        cv2.imwrite(output_path, processed_frame)
        print(f"Imagen procesada. Resultado guardado en {output_path}", flush=True)
        exit(0)

    if not video_source:
        print("No se configuró VIDEO_SOURCE. El servicio espera una fuente de video o IMAGE_SOURCE.", flush=True)
        while True:
            time.sleep(60)

    print(f"Fuente de video: {video_source}", flush=True)
    try:
        source = int(video_source)
    except ValueError:
        source = video_source

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"No se pudo abrir la fuente de video '{video_source}'. Esperando una fuente válida.", flush=True)
        while True:
            time.sleep(60)

    # Esperar a que la cámara se inicialice
    time.sleep(2)

    print("Sistema ALPR iniciado.", flush=True)
    if headless:
        print("Modo headless activado: no se abrirá ventana de salida.", flush=True)
    else:
        print("Presiona 'q' en la ventana para salir.", flush=True)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed_frame, readings = plate_reader.process_frame(frame, draw_rectangles=True)

            if not headless:
                cv2.imshow('ALPR - Reconocimiento de Placas', processed_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01)

    finally:
        cap.release()
        if not headless:
            cv2.destroyAllWindows()

        print("Sistema ALPR cerrado.")

if __name__ == "__main__":
    main()