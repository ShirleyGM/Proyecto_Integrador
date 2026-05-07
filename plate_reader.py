import cv2
import pytesseract
from datetime import datetime
import os

class PlateReader:
    def __init__(self, tesseract_cmd=None):
        """
        Inicializa el lector de placas vehiculares.
        
        Args:
            tesseract_cmd: Ruta a la instalación de Tesseract OCR (opcional)
        """
        # Si no se proporciona, buscar Tesseract automáticamente
        if not tesseract_cmd:
            tesseract_cmd = self._find_tesseract()
        
        self.tesseract_available = False
        if tesseract_cmd:
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                print(f"Tesseract configurado en: {tesseract_cmd}")
                self.tesseract_available = True
            else:
                print(f"Advertencia: Tesseract-OCR no encontrado en {tesseract_cmd}. El OCR no funcionará.")
        else:
            print("Advertencia: No se especificó ruta de Tesseract. El OCR no funcionará.")
        
        # Usar cascada de detección de rostros como fallback para detección general
        # Para mejores resultados, descarga una cascada específica para placas
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.plate_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.plate_cascade.empty():
            print("Advertencia: No se pudo cargar la cascada de clasificación.")
    
    def _find_tesseract(self):
        """
        Busca Tesseract-OCR en rutas comunes del sistema.
        
        Returns:
            Ruta a tesseract.exe si se encuentra, None en caso contrario
        """
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\BITGITAL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        ]
        
        # Verificar si hay una variable de entorno
        env_path = os.getenv('TESSERACT_CMD')
        if env_path and os.path.exists(env_path):
            return env_path
        
        # Buscar en rutas comunes
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Tesseract encontrado en: {path}")
                return path
        
        return None
    
    def detect_plates(self, image):
        """
        Detecta placas en una imagen.
        
        Args:
            image: Imagen de entrada (numpy array)
            
        Returns:
            Lista de tuplas (x, y, w, h) con las coordenadas de las placas detectadas
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        plates = self.plate_cascade.detectMultiScale(gray, 1.1, 4)
        return plates
    
    def recognize_text(self, plate_roi):
        """
        Realiza OCR en una región de placa.
        
        Args:
            plate_roi: Región de interés de la placa
            
        Returns:
            Texto reconocido (solo caracteres alfanuméricos)
        """
        if not self.tesseract_available:
            return None
            
        try:
            # Aplicar umbral para mejorar el OCR
            _, plate_roi_processed = cv2.threshold(plate_roi, 150, 255, cv2.THRESH_BINARY)
            
            # OCR
            text = pytesseract.image_to_string(plate_roi_processed, config='--psm 8')
            
            # Limpiar texto: solo alfanuméricos
            text = ''.join(e for e in text if e.isalnum())
            
            return text if text else None
        except Exception as e:
            print(f"Error en OCR: {e}")
            self.tesseract_available = False
            return None
    
    def process_frame(self, frame, draw_rectangles=True):
        """
        Procesa un frame detectando y reconociendo placas.
        
        Args:
            frame: Frame de video
            draw_rectangles: Si es True, dibuja rectángulos en las placas detectadas
            
        Returns:
            Tupla (frame procesado, lista de lecturas)
                donde cada lectura es un diccionario con:
                - 'texto': Texto reconocido
                - 'coords': (x, y, w, h)
                - 'timestamp': Marca de tiempo
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        plates = self.plate_cascade.detectMultiScale(gray, 1.1, 4)
        
        readings = []
        
        for (x, y, w, h) in plates:
            # Extraer la región de la placa
            plate_roi = gray[y:y+h, x:x+w]
            
            # Reconocer texto
            text = self.recognize_text(plate_roi)
            
            if draw_rectangles:
                # Dibujar rectángulo
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Mostrar texto o indicador de placa detectada
                display_text = text if text else "Placa detectada"
                cv2.putText(frame, display_text, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
            
            if text:
                readings.append({
                    'texto': text,
                    'coords': (x, y, w, h),
                    'timestamp': datetime.now()
                })
                print(f"Placa reconocida: {text}")
        
        return frame, readings
