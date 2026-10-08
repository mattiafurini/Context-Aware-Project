from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from api.schemas import (
    ContextSummaryResponse,
    PointCoordinates,
    ServicesCount,
    ClosestDistances,
    FeaturesNearby
)

router = APIRouter()

@router.get("/summary", response_model=ContextSummaryResponse, summary="Sintesi e densità contestuale dei servizi per un punto GPS")
def get_context_summary(
    lat: float = Query(..., ge=-90, le=90, description="Latitudine del punto selezionato"),
    lon: float = Query(..., ge=-180, le=180, description="Longitudine del punto selezionato"),
    radius: int = Query(500, ge=50, le=5000, description="Raggio di analisi contestuale in metri (default 500m)"),
    db: Session = Depends(get_db)
):
    """
    Esegue un'analisi context-aware aggregata del territorio circostante le coordinate fornite:
    - Conta la presenza di ciascuna categoria di servizio entro il raggio specificato (sedi Unibo, biblioteche, fermate TPER, parchi, piste ciclabili, rastrelliere).
    - Calcola la distanza minima precisa (in metri) per ogni tipologia di servizio.
    - Genera una sintesi qualitativa del contesto dell'area.
    Questo endpoint funge da base analitica per il calcolo dello score di accessibilità e del motore di raccomandazione.
    """
    params = {"lat": lat, "lon": lon, "radius": radius}

    # 1. Aggregazione POIs per categoria
    pois_sql = """
        SELECT 
            categoria,
            COUNT(*) AS cnt,
            MIN(ROUND(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 1)) AS min_dist
        FROM pois
        WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
        GROUP BY categoria;
    """
    pois_rows = db.execute(text(pois_sql), params).fetchall()

    poi_counts = {}
    poi_min_distances = {}
    for r in pois_rows:
        cat = (r.categoria or "altro").lower()
        poi_counts[cat] = int(r.cnt)
        poi_min_distances[cat] = float(r.min_dist) if r.min_dist is not None else None

    unibo_count = poi_counts.get("unibo", 0)
    unibo_min_dist = poi_min_distances.get("unibo")

    lib_count = poi_counts.get("biblioteca", 0)
    lib_min_dist = poi_min_distances.get("biblioteca")

    racks_count = poi_counts.get("rastrelliera", 0)
    racks_min_dist = poi_min_distances.get("rastrelliera")

    # 2. Aggregazione Mobilità (Fermate TPER e Piste ciclabili) e Aree Verdi
    infra_sql = """
        WITH center AS (
            SELECT ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS geog
        )
        SELECT 
            (SELECT count(*) FROM fermate_tper f, center c WHERE ST_DWithin(f.geom::geography, c.geog, :radius)) AS bus_stops,
            (SELECT min(round(ST_Distance(f.geom::geography, c.geog)::numeric, 1)) FROM fermate_tper f, center c WHERE ST_DWithin(f.geom::geography, c.geog, :radius)) AS min_bus_dist,
            (SELECT count(*) FROM piste_ciclabili pc, center c WHERE ST_DWithin(pc.geom::geography, c.geog, :radius)) AS bike_paths,
            (SELECT min(round(ST_Distance(pc.geom::geography, c.geog)::numeric, 1)) FROM piste_ciclabili pc, center c WHERE ST_DWithin(pc.geom::geography, c.geog, :radius)) AS min_bikepath_dist,
            (SELECT count(*) FROM aree_verdi av, center c WHERE ST_DWithin(av.geom::geography, c.geog, :radius)) AS green_areas,
            (SELECT min(round(ST_Distance(av.geom::geography, c.geog)::numeric, 1)) FROM aree_verdi av, center c WHERE ST_DWithin(av.geom::geography, c.geog, :radius)) AS min_green_dist;
    """
    infra_row = db.execute(text(infra_sql), params).fetchone()

    bus_count = int(infra_row.bus_stops) if infra_row and infra_row.bus_stops is not None else 0
    bus_min_dist = float(infra_row.min_bus_dist) if infra_row and infra_row.min_bus_dist is not None else None

    bikepath_count = int(infra_row.bike_paths) if infra_row and infra_row.bike_paths is not None else 0
    bikepath_min_dist = float(infra_row.min_bikepath_dist) if infra_row and infra_row.min_bikepath_dist is not None else None

    green_count = int(infra_row.green_areas) if infra_row and infra_row.green_areas is not None else 0
    green_min_dist = float(infra_row.min_green_dist) if infra_row and infra_row.min_green_dist is not None else None

    # 3. Generazione sintesi testuale intelligente del contesto
    features_desc = []
    if unibo_count > 0:
        dist_str = f"a {unibo_min_dist:.0f}m" if unibo_min_dist else ""
        features_desc.append(f"{unibo_count} sedi universitarie ({dist_str})")
    if lib_count > 0:
        dist_str = f"a {lib_min_dist:.0f}m" if lib_min_dist else ""
        features_desc.append(f"{lib_count} biblioteche ({dist_str})")
    if bus_count > 0:
        dist_str = f"a {bus_min_dist:.0f}m" if bus_min_dist else ""
        features_desc.append(f"{bus_count} fermate TPER ({dist_str})")
    if bikepath_count > 0:
        features_desc.append(f"collegamento a piste ciclabili ({bikepath_count} tratti)")
    if green_count > 0:
        dist_str = f"a {green_min_dist:.0f}m" if green_min_dist else ""
        features_desc.append(f"aree verdi e parchi ({dist_str})")

    if not features_desc:
        summary_text = f"Zona a bassa densità di servizi studenteschi entro {radius}m (nessun servizio principale rilevato nel raggio)."
    else:
        summary_text = f"Area con buona copertura entro {radius}m: " + "; ".join(features_desc) + "."

    return ContextSummaryResponse(
        coordinates=PointCoordinates(lat=lat, lon=lon),
        radius_meters=radius,
        services_count=ServicesCount(
            unibo_locations=unibo_count,
            libraries=lib_count,
            bus_stops=bus_count,
            bike_racks=racks_count,
            green_areas=green_count,
            bike_paths=bikepath_count
        ),
        closest_distances_meters=ClosestDistances(
            unibo_meters=unibo_min_dist,
            library_meters=lib_min_dist,
            bus_stop_meters=bus_min_dist,
            bike_rack_meters=racks_min_dist,
            green_area_meters=green_min_dist,
            bike_path_meters=bikepath_min_dist
        ),
        features_nearby=FeaturesNearby(
            has_unibo=unibo_count > 0,
            has_library=lib_count > 0,
            has_bus_stop=bus_count > 0,
            has_bike_rack=racks_count > 0,
            has_green_area=green_count > 0,
            has_bike_path=bikepath_count > 0
        ),
        summary_text=summary_text
    )
