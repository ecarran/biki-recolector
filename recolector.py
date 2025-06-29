import requests
import sqlite3
import datetime
from pytz import timezone

URL_STATUS = "https://valladolid.publicbikesystem.net/customer/gbfs/v2/en/station_status"
URL_INFO = "https://valladolid.publicbikesystem.net/customer/gbfs/v2/en/station_information"

def cargar_nombres_estaciones():
    try:
        response = requests.get(URL_INFO)
        data = response.json()
        return {e["station_id"]: e["name"] for e in data["data"]["stations"]}
    except:
        return {}

nombres_estaciones = cargar_nombres_estaciones()

def recolectar():
    try:
        response = requests.get(URL_STATUS)
        data = response.json()
        ahora = datetime.datetime.now(timezone('Europe/Madrid')).strftime("%Y-%m-%d %H:%M:%S")
        registros = []

        for est in data['data']['stations']:
            id_est = est['station_id']
            nombre = nombres_estaciones.get(id_est, id_est)
            total = est['num_bikes_available']
            docks = est['num_docks_available']
            bikes_disabled = est.get('num_bikes_disabled', 0)
            docks_disabled = est.get('num_docks_disabled', 0)

            electricas = 0
            normales = 0
            for tipo in est.get('vehicle_types_available', []):
                if tipo['vehicle_type_id'] == "EFIT":
                    electricas = tipo['count']
                elif tipo['vehicle_type_id'] == "FIT":
                    normales = tipo['count']

            registros.append((
                id_est, nombre, ahora, total, docks,
                bikes_disabled, docks_disabled,
                electricas, normales
            ))

        conn = sqlite3.connect("biki_data.db")
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estados (
            id TEXT,
            nombre TEXT,
            timestamp TEXT,
            num_bikes_available INTEGER,
            num_docks_available INTEGER,
            num_bikes_disabled INTEGER,
            num_docks_disabled INTEGER,
            electricas INTEGER,
            normales INTEGER
        )
        """)
        cursor.executemany("""
            INSERT INTO estados (
                id, nombre, timestamp,
                num_bikes_available, num_docks_available,
                num_bikes_disabled, num_docks_disabled,
                electricas, normales
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, registros)
        conn.commit()
        conn.close()
        print(f"{len(registros)} estaciones registradas a las {ahora}")
    except Exception as e:
        print("Error recolectando:", e)
