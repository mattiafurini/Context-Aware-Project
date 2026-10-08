import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from api.schemas import (
    ContextSummaryResponse,
    PointCoordinates,
    ServicesCount,
    ClosestDistances,
    FeaturesNearby,
    ScoreWeights,
    SubScores,
    TemporalContext,
    ScoreEvaluationRequest,
    ScoreEvaluationResponse
)

router = APIRouter()

def compute_spatial_aggregates(lat: float, lon: float, radius: int, db: Session):
    """Esegue le query geospaziali PostGIS indicizzate per aggregare conteggi e distanze minime."""
    params = {"lat": lat, "lon": lon, "radius": radius}

    # 1. POIs
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

    # 2. Mobilità e Aree Verdi
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

    return {
        "unibo_count": poi_counts.get("unibo", 0),
        "unibo_min_dist": poi_min_distances.get("unibo"),
        "lib_count": poi_counts.get("biblioteca", 0),
        "lib_min_dist": poi_min_distances.get("biblioteca"),
        "racks_count": poi_counts.get("rastrelliera", 0),
        "racks_min_dist": poi_min_distances.get("rastrelliera"),
        "bus_count": int(infra_row.bus_stops) if infra_row and infra_row.bus_stops is not None else 0,
        "bus_min_dist": float(infra_row.min_bus_dist) if infra_row and infra_row.min_bus_dist is not None else None,
        "bikepath_count": int(infra_row.bike_paths) if infra_row and infra_row.bike_paths is not None else 0,
        "bikepath_min_dist": float(infra_row.min_bikepath_dist) if infra_row and infra_row.min_bikepath_dist is not None else None,
        "green_count": int(infra_row.green_areas) if infra_row and infra_row.green_areas is not None else 0,
        "green_min_dist": float(infra_row.min_green_dist) if infra_row and infra_row.min_green_dist is not None else None,
    }


def evaluate_accessibility_score(
    lat: float,
    lon: float,
    radius: int,
    weights: ScoreWeights,
    hour: Optional[int],
    db: Session
) -> ScoreEvaluationResponse:
    """Calcola il punteggio pesato, applica filtri temporali e genera le motivazioni contestuali."""
    # 1. Determinazione contesto temporale
    current_hour = hour if hour is not None else datetime.now().hour
    if 8 <= current_hour < 20:
        scenario = "Diurno"
        is_night = False
        facilities_status = "Tutte le aule didattiche, biblioteche e linee TPER sono a pieno regime."
    elif 20 <= current_hour < 23:
        scenario = "Serale"
        is_night = False
        facilities_status = "Biblioteche in fase di chiusura; sale studio serali attive; frequenze bus ridotte."
    else:
        scenario = "Notturno"
        is_night = True
        facilities_status = "Biblioteche comunali chiuse; studio notturno limitato ad aule dedicate; servizio bus solo linee notturne."

    # 2. Aggregazione spaziale
    data = compute_spatial_aggregates(lat, lon, radius, db)

    # 3. Calcolo Sub-Score Settoriali normalizzati (0-100)
    # A) STUDIO (Sedi Unibo + Biblioteche)
    if data["unibo_min_dist"] is not None:
        prox_unibo = max(0.0, 100.0 - (data["unibo_min_dist"] - 50.0) * 0.15)
    else:
        prox_unibo = 0.0
    density_unibo = min(30.0, data["unibo_count"] * 2.5)
    lib_bonus = 25.0 if data["lib_count"] > 0 else 0.0
    sub_study = min(100.0, prox_unibo * 0.55 + density_unibo + lib_bonus)
    if is_night:
        sub_study *= 0.65 # Penalizzazione per chiusura serale/notturna biblioteche

    # B) TRASPORTI (Fermate TPER)
    if data["bus_min_dist"] is not None:
        prox_bus = max(0.0, 100.0 - (data["bus_min_dist"] - 50.0) * 0.18)
    else:
        prox_bus = 0.0
    density_bus = min(40.0, data["bus_count"] * 2.5)
    sub_transit = min(100.0, prox_bus * 0.60 + density_bus)
    if is_night:
        sub_transit *= 0.70 # Minore frequenza notturna

    # C) CICLABILITÀ (Piste Ciclabili + Rastrelliere)
    if data["bikepath_min_dist"] is not None:
        prox_bike = max(0.0, 100.0 - (data["bikepath_min_dist"] - 30.0) * 0.18)
    else:
        prox_bike = 0.0
    racks_bonus = min(35.0, data["racks_count"] * 1.5)
    sub_bike = min(100.0, prox_bike * 0.65 + racks_bonus)

    # D) AREE VERDI (Parchi e Relax)
    if data["green_min_dist"] is not None:
        prox_green = max(0.0, 100.0 - (data["green_min_dist"] - 50.0) * 0.16)
    else:
        prox_green = 0.0
    density_green = min(30.0, data["green_count"] * 15.0)
    sub_green = min(100.0, prox_green * 0.70 + density_green)

    # 4. Calcolo Punteggio Complessivo Pesato
    total_w = weights.study + weights.transit + weights.bike + weights.green
    if total_w <= 0:
        total_w = 100.0

    weighted_sum = (
        weights.study * sub_study +
        weights.transit * sub_transit +
        weights.bike * sub_bike +
        weights.green * sub_green
    )
    total_score = round(weighted_sum / total_w, 1)

    # 5. Classificazione Livello e Colore UI
    if total_score >= 85.0:
        rating_tier = "Eccellente"
        rating_color = "#10b981" # Emerald green
    elif total_score >= 70.0:
        rating_tier = "Molto Buono"
        rating_color = "#3b82f6" # Blue
    elif total_score >= 55.0:
        rating_tier = "Buono"
        rating_color = "#06b6d4" # Cyan
    elif total_score >= 40.0:
        rating_tier = "Sufficiente"
        rating_color = "#f59e0b" # Amber
    else:
        rating_tier = "Critico / Periferico"
        rating_color = "#ef4444" # Red

    # 6. Analisi dei Punti di Forza e Trade-Off
    strengths = []
    tradeoffs = []

    if sub_study >= 70.0:
        strengths.append(f"Altissima concentrazione di aule universitarie ({data['unibo_count']} sedi, più vicina a {data['unibo_min_dist']:.0f}m)")
    elif sub_study < 40.0:
        tradeoffs.append("Distanza consistente dalle principali sedi didattiche universitarie")

    if data["lib_count"] > 0 and not is_night:
        strengths.append(f"Biblioteca comunale a {data['lib_min_dist']:.0f}m con aule studio attive")
    elif data["lib_count"] > 0 and is_night:
        tradeoffs.append("Biblioteche dell'area non accessibili nell'orario notturno selezionato")

    if sub_transit >= 70.0:
        strengths.append(f"Collegamento eccellente TPER ({data['bus_count']} fermate, prima fermata a {data['bus_min_dist']:.0f}m)")
    elif sub_transit < 40.0:
        tradeoffs.append("Rete di autobus locale a bassa densità nelle immediate vicinanze")

    if sub_bike >= 65.0:
        strengths.append(f"Mobilità ciclabile ideale: corsie ciclabili a {data['bikepath_min_dist']:.0f}m e {data['racks_count']} rastrelliere")
    elif sub_bike < 40.0:
        tradeoffs.append("Carenza di piste ciclabili protette o rastrelliere per sosta sicura")

    if sub_green >= 60.0:
        strengths.append(f"Presenza di parchi e aree verdi per pause all'aperto ({data['green_min_dist']:.0f}m)")
    elif sub_green < 35.0:
        tradeoffs.append("Zona urbana densa con scarsa dotazione di verde pubblico nelle vicinanze")

    if not strengths:
        strengths.append("Area tranquilla a basso impatto di traffico studentesco")
    if not tradeoffs:
        tradeoffs.append("Nessun deficit strutturale significativo rilevato nel raggio impostato")

    # 7. Generazione Raccomandazione Esplicita Contestuale
    # Individuiamo la priorità dominante scelta dallo studente
    weight_dict = {"studio": weights.study, "trasporti": weights.transit, "bici": weights.bike, "verde": weights.green}
    top_priority = max(weight_dict, key=weight_dict.get)

    if total_score >= 80.0:
        rec_prefix = f"Area fortemente consigliata per il tuo profilo (focus: {top_priority.capitalize()}): "
        if top_priority == "studio":
            rec_body = "perfetta per chi desidera minimizzare i tempi di spostamento e vivere nel cuore della vita universitaria."
        elif top_priority == "trasporti":
            rec_body = "ideale per studenti pendolari o per raggiungere rapidamente qualsiasi quartiere della città."
        elif top_priority == "bici":
            rec_body = "scenario ottimale per chi si sposta quotidianamente sulle due ruote in piena sicurezza."
        else:
            rec_body = "combinazione ideale tra servizi universitari e benessere all'aria aperta."
    elif total_score >= 55.0:
        rec_prefix = "Area discretamente servita con buon compromesso complessivo: "
        rec_body = "consigliata per chi cerca un equilibrio tra vita quotidiana e accessibilità accademica, tenendo conto dei trade-off segnalati."
    else:
        rec_prefix = "Area a bassa accessibilità per le preferenze indicate: "
        rec_body = "richiederà maggiori tempi di percorrenza per raggiungere aule didattiche e nodi di trasporto principali."

    recommendation_text = rec_prefix + rec_body

    return ScoreEvaluationResponse(
        coordinates=PointCoordinates(lat=lat, lon=lon),
        radius_meters=radius,
        total_score=total_score,
        rating_tier=rating_tier,
        rating_color=rating_color,
        sub_scores=SubScores(
            study=round(sub_study, 1),
            transit=round(sub_transit, 1),
            bike=round(sub_bike, 1),
            green=round(sub_green, 1)
        ),
        applied_weights=weights,
        temporal_context=TemporalContext(
            hour=current_hour,
            scenario=scenario,
            is_night=is_night,
            facilities_open_status=facilities_status
        ),
        strengths=strengths,
        tradeoffs=tradeoffs,
        recommendation_text=recommendation_text
    )


@router.get("/summary", response_model=ContextSummaryResponse, summary="Sintesi e densità contestuale dei servizi per un punto GPS")
def get_context_summary(
    lat: float = Query(..., ge=-90, le=90, description="Latitudine del punto selezionato"),
    lon: float = Query(..., ge=-180, le=180, description="Longitudine del punto selezionato"),
    radius: int = Query(500, ge=50, le=5000, description="Raggio di analisi contestuale in metri (default 500m)"),
    db: Session = Depends(get_db)
):
    """Restituisce il riassunto quantitativo e le distanze minime di tutti i servizi nel raggio."""
    data = compute_spatial_aggregates(lat, lon, radius, db)

    features_desc = []
    if data["unibo_count"] > 0:
        dist_str = f"a {data['unibo_min_dist']:.0f}m" if data["unibo_min_dist"] else ""
        features_desc.append(f"{data['unibo_count']} sedi universitarie ({dist_str})")
    if data["lib_count"] > 0:
        dist_str = f"a {data['lib_min_dist']:.0f}m" if data["lib_min_dist"] else ""
        features_desc.append(f"{data['lib_count']} biblioteche ({dist_str})")
    if data["bus_count"] > 0:
        dist_str = f"a {data['bus_min_dist']:.0f}m" if data["bus_min_dist"] else ""
        features_desc.append(f"{data['bus_count']} fermate TPER ({dist_str})")
    if data["bikepath_count"] > 0:
        features_desc.append(f"collegamento a piste ciclabili ({data['bikepath_count']} tratti)")
    if data["green_count"] > 0:
        dist_str = f"a {data['green_min_dist']:.0f}m" if data["green_min_dist"] else ""
        features_desc.append(f"aree verdi e parchi ({dist_str})")

    if not features_desc:
        summary_text = f"Zona a bassa densità di servizi studenteschi entro {radius}m."
    else:
        summary_text = f"Area con buona copertura entro {radius}m: " + "; ".join(features_desc) + "."

    return ContextSummaryResponse(
        coordinates=PointCoordinates(lat=lat, lon=lon),
        radius_meters=radius,
        services_count=ServicesCount(
            unibo_locations=data["unibo_count"],
            libraries=data["lib_count"],
            bus_stops=data["bus_count"],
            bike_racks=data["racks_count"],
            green_areas=data["green_count"],
            bike_paths=data["bikepath_count"]
        ),
        closest_distances_meters=ClosestDistances(
            unibo_meters=data["unibo_min_dist"],
            library_meters=data["lib_min_dist"],
            bus_stop_meters=data["bus_min_dist"],
            bike_rack_meters=data["racks_min_dist"],
            green_area_meters=data["green_min_dist"],
            bike_path_meters=data["bikepath_min_dist"]
        ),
        features_nearby=FeaturesNearby(
            has_unibo=data["unibo_count"] > 0,
            has_library=data["lib_count"] > 0,
            has_bus_stop=data["bus_count"] > 0,
            has_bike_rack=data["racks_count"] > 0,
            has_green_area=data["green_count"] > 0,
            has_bike_path=data["bikepath_count"] > 0
        ),
        summary_text=summary_text
    )


@router.post("/evaluate", response_model=ScoreEvaluationResponse, summary="Calcola lo Student Accessibility Score pesato con raccomandazione esplicita (POST)")
def evaluate_accessibility_post(
    request: ScoreEvaluationRequest,
    db: Session = Depends(get_db)
):
    """Valuta l'accessibilità urbana e genera raccomandazioni personalizzate (payload JSON)."""
    weights = request.weights or ScoreWeights()
    return evaluate_accessibility_score(
        lat=request.lat,
        lon=request.lon,
        radius=request.radius,
        weights=weights,
        hour=request.hour,
        db=db
    )


@router.get("/evaluate", response_model=ScoreEvaluationResponse, summary="Calcola lo Student Accessibility Score pesato con raccomandazione esplicita (GET)")
def evaluate_accessibility_get(
    lat: float = Query(..., ge=-90, le=90, description="Latitudine"),
    lon: float = Query(..., ge=-180, le=180, description="Longitudine"),
    radius: int = Query(500, ge=50, le=5000, description="Raggio in metri"),
    weight_study: float = Query(40.0, ge=0, le=100, description="Peso Studio (0-100)"),
    weight_transit: float = Query(30.0, ge=0, le=100, description="Peso Trasporti (0-100)"),
    weight_bike: float = Query(20.0, ge=0, le=100, description="Peso Ciclabilità (0-100)"),
    weight_green: float = Query(10.0, ge=0, le=100, description="Peso Aree Verdi (0-100)"),
    hour: Optional[int] = Query(None, ge=0, le=23, description="Ora (0-23) o orario corrente"),
    db: Session = Depends(get_db)
):
    """Valuta l'accessibilità urbana e genera raccomandazioni tramite parametri di query GET."""
    weights = ScoreWeights(
        study=weight_study,
        transit=weight_transit,
        bike=weight_bike,
        green=weight_green
    )
    return evaluate_accessibility_score(
        lat=lat,
        lon=lon,
        radius=radius,
        weights=weights,
        hour=hour,
        db=db
    )
