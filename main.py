from fastapi import FastAPI
from fastapi.responses import FileResponse
from recolector import recolectar

app = FastAPI()

@app.get("/")
def home():
    return {"mensaje": "API de recolección BIKI operativa. Usa /recolectar para ejecutar."}

@app.get("/recolectar")
def lanzar_recoleccion():
    try:
        recolectar()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}

@app.get("/descargar-db")
def descargar_db():
    return FileResponse("biki_data.db", media_type='application/octet-stream', filename="biki_data.db")

