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

        conn = sqlite3.connect("biki_data.db")
        cursor = conn.cursor()

        # Crear tabla si no existe
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
            normales INTEGER,
            total_bicis INTEGER,
            deltaBicis INTEGER
        )
        """)

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

            total_bicis = electricas + normales

            # Obtener último valor previo
            cursor.execute("""
                SELECT total_bicis FROM estados
                WHERE id = ? ORDER BY timestamp DESC LIMIT 1
            """, (id_est,))
            row = cursor.fetchone()
            anterior = row[0] if row else None
            delta = total_bicis - anterior if anterior is not None else None

            registros.append((
                id_est, nombre, ahora, total, docks,
                bikes_disabled, docks_disabled,
                electricas, normales, total_bicis, delta
            ))

        cursor.executemany("""
            INSERT INTO estados (
                id, nombre, timestamp,
                num_bikes_available, num_docks_available,
                num_bikes_disabled, num_docks_disabled,
                electricas, normales, total_bicis, deltaBicis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, registros)

        # Crear índice si no existe (re-aplicable sin duplicación)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_estados_station_time 
            ON estados (id, timestamp)
        """)

        conn.commit()
        conn.close()
        print(f"{len(registros)} estaciones registradas a las {ahora}")
    except Exception as e:
        print("Error recolectando:", e)

recolectar()

