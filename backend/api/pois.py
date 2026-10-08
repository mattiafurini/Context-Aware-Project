from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from api.schemas import POINearbyResponse, POIItem, PointCoordinates

router = APIRouter()

@router.get("/categories", response_model=List[str], summary="Elenco categorie POI disponibili")
def get_categories(db: Session = Depends(get_db)):
    """Restituisce l'elenco delle categorie univoche presenti nel database."""
    query = text("SELECT DISTINCT categoria FROM pois WHERE categoria IS NOT NULL ORDER BY categoria ASC;")
    result = db.execute(query).fetchall()
    return [row[0] for row in result]

@router.get("/nearby", response_model=POINearbyResponse, summary="Ricerca POI entro un raggio (in metri)")
def get_pois_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitudine del punto centrale (es. 44.4965)"),
    lon: float = Query(..., ge=-180, le=180, description="Longitudine del punto centrale (es. 11.3533)"),
    radius: int = Query(500, ge=50, le=10000, description="Raggio di ricerca in metri (default: 500m)"),
    categoria: Optional[str] = Query(None, description="Filtro per categoria (es. unibo, biblioteca, rastrelliera, museo)"),
    limit: int = Query(100, ge=1, le=500, description="Numero massimo di risultati da restituire"),
    db: Session = Depends(get_db)
):
    """
    Esegue una query geospaziale su PostGIS per trovare tutti i Punti di Interesse (POIs)
    entro il raggio specificato, calcolando la distanza precisa in metri per ciascuno.
    """
    sql = """
        SELECT 
            id,
            nome,
            categoria,
            indirizzo,
            ST_Y(geom) AS lat,
            ST_X(geom) AS lon,
            ROUND(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 1) AS distance_meters
        FROM pois
        WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
          AND (:categoria IS NULL OR LOWER(categoria) = LOWER(:categoria))
        ORDER BY distance_meters ASC
        LIMIT :limit;
    """

    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "categoria": categoria,
        "limit": limit
    }

    rows = db.execute(text(sql), params).fetchall()

    results = [
        POIItem(
            id=row.id,
            nome=row.nome,
            categoria=row.categoria,
            indirizzo=row.indirizzo,
            lat=float(row.lat),
            lon=float(row.lon),
            distance_meters=float(row.distance_meters)
        )
        for row in rows
    ]

    return POINearbyResponse(
        total=len(results),
        radius_meters=radius,
        center=PointCoordinates(lat=lat, lon=lon),
        results=results
    )

@router.get("/{poi_id}", response_model=POIItem, summary="Dettaglio singolo POI")
def get_poi_by_id(poi_id: int, db: Session = Depends(get_db)):
    """Restituisce le informazioni di un singolo POI dato il suo ID."""
    sql = """
        SELECT 
            id,
            nome,
            categoria,
            indirizzo,
            ST_Y(geom) AS lat,
            ST_X(geom) AS lon
        FROM pois
        WHERE id = :id;
    """
    row = db.execute(text(sql), {"id": poi_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="POI non trovato")
    
    return POIItem(
        id=row.id,
        nome=row.nome,
        categoria=row.categoria,
        indirizzo=row.indirizzo,
        lat=float(row.lat),
        lon=float(row.lon),
        distance_meters=0.0
    )
