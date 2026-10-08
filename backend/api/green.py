from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from api.schemas import GreenAreaNearbyResponse, GreenAreaItem, PointCoordinates

router = APIRouter()

@router.get("/areas", summary="Aree verdi e parchi in formato GeoJSON")
def get_green_areas_geojson(
    min_lon: Optional[float] = Query(None, description="Bounding Box: Longitudine Ovest"),
    min_lat: Optional[float] = Query(None, description="Bounding Box: Latitudine Sud"),
    max_lon: Optional[float] = Query(None, description="Bounding Box: Longitudine Est"),
    max_lat: Optional[float] = Query(None, description="Bounding Box: Latitudine Nord"),
    limit: int = Query(500, ge=1, le=2000, description="Numero massimo di aree verdi"),
    db: Session = Depends(get_db)
):
    """
    Restituisce i parchi e le aree verdi di Bologna come GeoJSON FeatureCollection,
    direttamente consumabile da Leaflet.js per la visualizzazione dei layer.
    """
    has_bbox = all(v is not None for v in [min_lon, min_lat, max_lon, max_lat])

    if has_bbox:
        sql = """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'id', id,
                        'geometry', ST_AsGeoJSON(geom)::json,
                        'properties', json_build_object(
                            'id', id,
                            'nome', nome
                        )
                    )
                ), '[]'::json)
            )::text AS geojson
            FROM (
                SELECT id, nome, geom
                FROM aree_verdi
                WHERE geom && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
                LIMIT :limit
            ) sub;
        """
        params = {
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat,
            "limit": limit
        }
    else:
        sql = """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'id', id,
                        'geometry', ST_AsGeoJSON(geom)::json,
                        'properties', json_build_object(
                            'id', id,
                            'nome', nome
                        )
                    )
                ), '[]'::json)
            )::text AS geojson
            FROM (
                SELECT id, nome, geom
                FROM aree_verdi
                LIMIT :limit
            ) sub;
        """
        params = {"limit": limit}

    row = db.execute(text(sql), params).fetchone()
    geojson_data = row[0] if row and row[0] else '{"type": "FeatureCollection", "features": []}'

    return Response(content=geojson_data, media_type="application/json")

@router.get("/nearby", response_model=GreenAreaNearbyResponse, summary="Ricerca aree verdi vicine con calcolo distanza")
def get_green_areas_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitudine centrale"),
    lon: float = Query(..., ge=-180, le=180, description="Longitudine centrale"),
    radius: int = Query(600, ge=50, le=5000, description="Raggio di ricerca in metri (default: 600m)"),
    limit: int = Query(50, ge=1, le=200, description="Numero massimo di aree"),
    db: Session = Depends(get_db)
):
    """
    Trova le aree verdi e i parchi entro il raggio specificato,
    calcolando la distanza minima dal punto fornito e il baricentro del parco.
    """
    sql = """
        SELECT 
            id,
            nome,
            ST_Y(ST_Centroid(geom)) AS lat,
            ST_X(ST_Centroid(geom)) AS lon,
            ROUND(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 1) AS distance_meters
        FROM aree_verdi
        WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
        ORDER BY distance_meters ASC
        LIMIT :limit;
    """

    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "limit": limit
    }

    rows = db.execute(text(sql), params).fetchall()

    results = [
        GreenAreaItem(
            id=row.id,
            nome=row.nome or "Area Verde",
            lat=float(row.lat) if row.lat is not None else None,
            lon=float(row.lon) if row.lon is not None else None,
            distance_meters=float(row.distance_meters)
        )
        for row in rows
    ]

    return GreenAreaNearbyResponse(
        total=len(results),
        radius_meters=radius,
        center=PointCoordinates(lat=lat, lon=lon),
        results=results
    )
