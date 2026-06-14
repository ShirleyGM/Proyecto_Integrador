import cv2

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None


class VehicleLookup:
    def __init__(self, mongo_uri):
        self.collection = None
        if MongoClient is None:
            return
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            self.collection = client['alpr_db']['vehiculos']
            print("✓ VehicleLookup conectado a colección 'vehiculos'", flush=True)
        except Exception as e:
            print(f"⚠ VehicleLookup sin conexión a MongoDB: {e}", flush=True)

    def find_by_plate(self, plate: str) -> dict | None:
        if self.collection is None:
            return None
        try:
            return self.collection.find_one({"numero_placa": plate}, {"_id": 0})
        except Exception:
            return None

    def draw_info(self, frame, coords, vehicle: dict | None):
        x, y, w, h = coords

        if vehicle:
            conductor = vehicle.get("conductor", {})
            lines = [
                f"Placa : {vehicle.get('numero_placa', '-')}",
                f"Tipo  : {vehicle.get('tipo_vehiculo', '-')}",
                f"Carga : {vehicle.get('tipo_carga', '-')}",
                f"Cond. : {conductor.get('nombre', '-')}",
                f"Tel.  : {conductor.get('telefono', '-')}",
            ]
            box_color = (30, 180, 30)
            border_color = (0, 220, 0)
        else:
            lines = ["Vehiculo no registrado"]
            box_color = (30, 30, 180)
            border_color = (0, 0, 220)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.52
        thickness = 1
        line_h = 22
        padding = 8

        box_w = 270
        box_h = len(lines) * line_h + padding * 2

        # Posicionar debajo de la placa; subir si se sale del frame
        bx = x
        by = y + h + 6
        if by + box_h > frame.shape[0]:
            by = y - box_h - 6

        # Fondo semitransparente
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h), box_color, -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        # Borde
        cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), border_color, 1)

        # Texto
        for i, line in enumerate(lines):
            ty = by + padding + (i + 1) * line_h - 4
            cv2.putText(frame, line, (bx + padding, ty), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
