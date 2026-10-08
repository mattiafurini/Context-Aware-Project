from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from api import pois, mobility, green, context

app = FastAPI(
    title="Student Urban Accessibility API",
    description="Backend API con calcolo spaziale PostGIS per la mobilità studentesca a Bologna",
    version="1.0.0"
)

# Configurazione CORS per consentire chiamate dal frontend (es. Nginx su porta 8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione può essere ristretto a ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrazione Router Modulari
app.include_router(pois.router, prefix="/api/pois", tags=["Punti di Interesse (POIs)"])
app.include_router(mobility.router, prefix="/api/mobility", tags=["Mobilità & Trasporti"])
app.include_router(green.router, prefix="/api/green", tags=["Aree Verdi & Parchi"])
app.include_router(context.router, prefix="/api/context", tags=["Contesto & Analytics"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Student Urban Accessibility API attiva",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Verifica lo stato del server e della connessione al database PostGIS."""
    try:
        result = db.execute(text("SELECT PostGIS_Version();")).scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "postgis_version": result
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database_error": str(e)
        }
