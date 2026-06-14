import cv2
import pytesseract
from datetime import datetime
import os

class PlateReader:
    def __init__(self, tesseract_cmd=None):
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

    def _find_tesseract(self):
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]

        env_path = os.getenv('TESSERACT_CMD')
        if env_path and os.path.exists(env_path):
            return env_path

        for path in possible_paths:
            if os.path.exists(path):
                print(f"Tesseract encontrado en: {path}")
                return path

        return None

    def detect_plates(self, gray):
        """
        Detecta placas en una imagen en escala de grises usando contornos y proporciones.

        Args:
            gray: Imagen en escala de grises (numpy array)

        Returns:
            Lista de tuplas (x, y, w, h) sin solapamientos
        """
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        edges = cv2.Canny(enhanced, 100, 200)

        # RETR_EXTERNAL: solo contornos exteriores, evita duplicados anidados
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1500:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            if w < 60 or h < 15:
                continue

            ratio = w / h
            if 2.5 < ratio < 5.5:
                candidates.append((x, y, w, h))

        return self._nms(candidates)

    def _nms(self, boxes, overlap_threshold=0.5):
        """Elimina regiones solapadas, conservando la de mayor área."""
        if not boxes:
            return []

        boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
        kept = []

        for box in boxes:
            x1, y1, w1, h1 = box
            dominated = False
            for kx, ky, kw, kh in kept:
                ix = max(0, min(x1 + w1, kx + kw) - max(x1, kx))
                iy = max(0, min(y1 + h1, ky + kh) - max(y1, ky))
                intersection = ix * iy
                union = w1 * h1 + kw * kh - intersection
                if union > 0 and intersection / union > overlap_threshold:
                    dominated = True
                    break
            if not dominated:
                kept.append(box)

        return kept

    def recognize_text(self, plate_roi):
        """
        Realiza OCR en una región de placa.

        Args:
            plate_roi: Región de interés en escala de grises

        Returns:
            Tupla (texto, confianza) donde texto es str o None y confianza es float 0–1
        """
        if not self.tesseract_available:
            return None, 0.0

        try:
            _, plate_bin = cv2.threshold(plate_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            config = '--psm 7 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            data = pytesseract.image_to_data(plate_bin, config=config, output_type=pytesseract.Output.DICT)

            confidences = [c for c in data['conf'] if c != -1]
            text = ''.join(e for e in ' '.join(data['text']).strip() if e.isalnum())
            confidence = round(sum(confidences) / len(confidences) / 100.0, 3) if confidences else 0.0

            return (text if text else None), confidence
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None, 0.0

    def process_frame(self, frame, draw_rectangles=True):
        """
        Procesa un frame detectando y reconociendo placas.

        Args:
            frame: Frame de video (BGR)
            draw_rectangles: Si es True, dibuja rectángulos en las placas detectadas

        Returns:
            Tupla (frame procesado, lista de lecturas)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        plates = self.detect_plates(gray)

        readings = []

        for (x, y, w, h) in plates:
            plate_roi = gray[y:y+h, x:x+w]
            text, confidence = self.recognize_text(plate_roi)

            if draw_rectangles:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                display_text = text if text else "Placa detectada"
                cv2.putText(frame, display_text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

            if text:
                readings.append({
                    'texto': text,
                    'coords': (x, y, w, h),
                    'timestamp': datetime.now(),
                    'confianza': confidence,
                })
                print(f"Placa reconocida: {text} (confianza: {confidence:.1%})")

        return frame, readings
