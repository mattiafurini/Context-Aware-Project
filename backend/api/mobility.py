from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
import json

from database import get_db
from api.schemas import BusStopNearbyResponse, BusStopItem, PointCoordinates

router = APIRouter()

@router.get("/stops/nearby", response_model=BusStopNearbyResponse, summary="Ricerca fermate TPER entro un raggio (in metri)")
def get_bus_stops_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitudine centrale"),
    lon: float = Query(..., ge=-180, le=180, description="Longitudine centrale"),
    radius: int = Query(400, ge=50, le=5000, description="Raggio di ricerca in metri (default: 400m)"),
    limit: int = Query(100, ge=1, le=500, description="Numero massimo di fermate da restituire"),
    db: Session = Depends(get_db)
):
    """
    Interroga le fermate del trasporto pubblico locale (feed GTFS TPER)
    entro il raggio indicato, calcolando la distanza precisa per ciascuna fermata.
    """
    sql = """
        SELECT 
            id_fermata,
            nome_fermata,
            ST_Y(geom) AS lat,
            ST_X(geom) AS lon,
            ROUND(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 1) AS distance_meters
        FROM fermate_tper
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
        BusStopItem(
            id_fermata=str(row.id_fermata),
            nome_fermata=row.nome_fermata,
            lat=float(row.lat),
            lon=float(row.lon),
            distance_meters=float(row.distance_meters)
        )
        for row in rows
    ]

    return BusStopNearbyResponse(
        total=len(results),
        radius_meters=radius,
        center=PointCoordinates(lat=lat, lon=lon),
        results=results
    )

@router.get("/bikepaths", summary="Tracciati piste ciclabili in formato GeoJSON")
def get_bikepaths_geojson(
    min_lon: Optional[float] = Query(None, description="Bounding Box: Longitudine Ovest"),
    min_lat: Optional[float] = Query(None, description="Bounding Box: Latitudine Sud"),
    max_lon: Optional[float] = Query(None, description="Bounding Box: Longitudine Est"),
    max_lat: Optional[float] = Query(None, description="Bounding Box: Latitudine Nord"),
    limit: int = Query(1000, ge=1, le=5000, description="Limite massimo di segmenti ciclabili"),
    db: Session = Depends(get_db)
):
    """
    Restituisce i tracciati delle piste ciclabili come GeoJSON FeatureCollection,
    pronto per essere renderizzato direttamente sulla mappa Leaflet.js.
    Se specificato un Bounding Box (bbox), filtra solo i segmenti visibili nella mappa.
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
                            'tipologia', tipologia
                        )
                    )
                ), '[]'::json)
            )::text AS geojson
            FROM (
                SELECT id, tipologia, geom
                FROM piste_ciclabili
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
                            'tipologia', tipologia
                        )
                    )
                ), '[]'::json)
            )::text AS geojson
            FROM (
                SELECT id, tipologia, geom
                FROM piste_ciclabili
                LIMIT :limit
            ) sub;
        """
        params = {"limit": limit}

    row = db.execute(text(sql), params).fetchone()
    geojson_data = row[0] if row and row[0] else '{"type": "FeatureCollection", "features": []}'

    return Response(content=geojson_data, media_type="application/json")
