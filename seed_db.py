import os
from pymongo import MongoClient, ASCENDING
from datetime import datetime

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo_user:mongo_pass@localhost:27017/alpr_db?authSource=admin')

VEHICULOS = [
    {
        "numero_placa": "ABC1234",
        "tipo_vehiculo": "Camión",
        "tipo_carga": "Balanceado",
        "conductor": {"nombre": "Carlos Martínez", "cedula": "10234567", "telefono": "3101234567"},
    },
    {
        "numero_placa": "DEF5678",
        "tipo_vehiculo": "Tractomula",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "Luis Herrera", "cedula": "10345678", "telefono": "3112345678"},
    },
    {
        "numero_placa": "GHI9012",
        "tipo_vehiculo": "Furgón",
        "tipo_carga": "Balanceado",
        "conductor": {"nombre": "Jorge Ramírez", "cedula": "10456789", "telefono": "3123456789"},
    },
    {
        "numero_placa": "JKL3456",
        "tipo_vehiculo": "Camioneta",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "Andrés López", "cedula": "10567890", "telefono": "3134567890"},
    },
    {
        "numero_placa": "MNO7890",
        "tipo_vehiculo": "Van",
        "tipo_carga": "Concentrado",
        "conductor": {"nombre": "Ricardo Gómez", "cedula": "10678901", "telefono": "3145678901"},
    },
    {
        "numero_placa": "PQR1357",
        "tipo_vehiculo": "Camión",
        "tipo_carga": "Maíz",
        "conductor": {"nombre": "Fabián Torres", "cedula": "10789012", "telefono": "3156789012"},
    },
    {
        "numero_placa": "STU2468",
        "tipo_vehiculo": "Tractomula",
        "tipo_carga": "Soya",
        "conductor": {"nombre": "Mauricio Vargas", "cedula": "10890123", "telefono": "3167890123"},
    },
    {
        "numero_placa": "VWX3691",
        "tipo_vehiculo": "Furgón",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "Nelson Castillo", "cedula": "10901234", "telefono": "3178901234"},
    },
    {
        "numero_placa": "YZA4802",
        "tipo_vehiculo": "Camioneta",
        "tipo_carga": "Balanceado",
        "conductor": {"nombre": "Sergio Moreno", "cedula": "11012345", "telefono": "3189012345"},
    },
    {
        "numero_placa": "BCD5913",
        "tipo_vehiculo": "Camión",
        "tipo_carga": "Concentrado",
        "conductor": {"nombre": "Diego Peña", "cedula": "11123456", "telefono": "3190123456"},
    },
    {
        "numero_placa": "EFG6024",
        "tipo_vehiculo": "Van",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "Camilo Ríos", "cedula": "11234567", "telefono": "3201234567"},
    },
    {
        "numero_placa": "HIJ7135",
        "tipo_vehiculo": "Tractomula",
        "tipo_carga": "Maíz",
        "conductor": {"nombre": "Hernán Suárez", "cedula": "11345678", "telefono": "3212345678"},
    },
    {
        "numero_placa": "KLM8246",
        "tipo_vehiculo": "Camión",
        "tipo_carga": "Balanceado",
        "conductor": {"nombre": "Óscar Jiménez", "cedula": "11456789", "telefono": "3223456789"},
    },
    {
        "numero_placa": "NOP9357",
        "tipo_vehiculo": "Furgón",
        "tipo_carga": "Soya",
        "conductor": {"nombre": "Iván Medina", "cedula": "11567890", "telefono": "3234567890"},
    },
    {
        "numero_placa": "QRS0468",
        "tipo_vehiculo": "Camioneta",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "Julián Ramos", "cedula": "11678901", "telefono": "3245678901"},
    },
    {
        "numero_placa": "TUV1579",
        "tipo_vehiculo": "Van",
        "tipo_carga": "Concentrado",
        "conductor": {"nombre": "Rodrigo Salcedo", "cedula": "11789012", "telefono": "3256789012"},
    },
    {
        "numero_placa": "WXY2680",
        "tipo_vehiculo": "Camión",
        "tipo_carga": "Balanceado",
        "conductor": {"nombre": "Alejandro Cruz", "cedula": "11890123", "telefono": "3267890123"},
    },
    {
        "numero_placa": "ZAB3791",
        "tipo_vehiculo": "Tractomula",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "Fernando Rojas", "cedula": "11901234", "telefono": "3278901234"},
    },
    {
        "numero_placa": "CDE4802",
        "tipo_vehiculo": "Furgón",
        "tipo_carga": "Maíz",
        "conductor": {"nombre": "Gustavo Parra", "cedula": "12012345", "telefono": "3289012345"},
    },
    {
        "numero_placa": "FGH5913",
        "tipo_vehiculo": "Camioneta",
        "tipo_carga": "Soya",
        "conductor": {"nombre": "Pablo Ortega", "cedula": "12123456", "telefono": "3290123456"},
    },
    {
        "numero_placa": "AAC0123",
        "tipo_vehiculo": "Camión",
        "tipo_carga": "Pollos",
        "conductor": {"nombre": "William Fuentes", "cedula": "12234567", "telefono": "3201357924"},
    },
]


def seed():
    print("Conectando a MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
    except Exception as e:
        print(f"✗ No se pudo conectar a MongoDB: {e}")
        return

    db = client['alpr_db']
    col = db['vehiculos']

    # Índice único sobre numero_placa para evitar duplicados
    col.create_index([('numero_placa', ASCENDING)], unique=True)

    insertados = 0
    omitidos = 0

    for v in VEHICULOS:
        doc = {**v, "fecha_registro": datetime.utcnow()}
        try:
            col.update_one(
                {"numero_placa": v["numero_placa"]},
                {"$setOnInsert": doc},
                upsert=True,
            )
            insertados += 1
        except Exception as e:
            print(f"  ⚠ Error con placa {v['numero_placa']}: {e}")
            omitidos += 1

    total = col.count_documents({})
    print(f"✓ Seed completado: {insertados} procesados, {omitidos} errores.")
    print(f"  Total en colección 'vehiculos': {total} registros.")
    client.close()


if __name__ == '__main__':
    seed()
