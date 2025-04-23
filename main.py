from fastapi import FastAPI
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
