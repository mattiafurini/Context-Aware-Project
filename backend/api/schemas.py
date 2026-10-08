from typing import Optional, List
from pydantic import BaseModel, Field

class PointCoordinates(BaseModel):
    lat: float = Field(..., description="Latitudine WGS84")
    lon: float = Field(..., description="Longitudine WGS84")

class POIItem(BaseModel):
    id: int
    nome: str
    categoria: Optional[str] = None
    indirizzo: Optional[str] = None
    lat: float
    lon: float
    distance_meters: float

class POINearbyResponse(BaseModel):
    total: int
    radius_meters: int
    center: PointCoordinates
    results: List[POIItem]

class BusStopItem(BaseModel):
    id_fermata: str
    nome_fermata: str
    lat: float
    lon: float
    distance_meters: float

class BusStopNearbyResponse(BaseModel):
    total: int
    radius_meters: int
    center: PointCoordinates
    results: List[BusStopItem]

class GreenAreaItem(BaseModel):
    id: int
    nome: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance_meters: float

class GreenAreaNearbyResponse(BaseModel):
    total: int
    radius_meters: int
    center: PointCoordinates
    results: List[GreenAreaItem]

class ServicesCount(BaseModel):
    unibo_locations: int = Field(0, description="Numero di sedi universitarie e dipartimenti")
    libraries: int = Field(0, description="Numero di biblioteche comunali")
    bus_stops: int = Field(0, description="Numero di fermate TPER")
    bike_racks: int = Field(0, description="Numero di rastrelliere per biciclette")
    green_areas: int = Field(0, description="Numero di parchi e aree verdi")
    bike_paths: int = Field(0, description="Numero di segmenti di piste ciclabili")

class ClosestDistances(BaseModel):
    unibo_meters: Optional[float] = Field(None, description="Distanza dalla sede Unibo più vicina (m)")
    library_meters: Optional[float] = Field(None, description="Distanza dalla biblioteca più vicina (m)")
    bus_stop_meters: Optional[float] = Field(None, description="Distanza dalla fermata TPER più vicina (m)")
    bike_rack_meters: Optional[float] = Field(None, description="Distanza dalla rastrelliera più vicina (m)")
    green_area_meters: Optional[float] = Field(None, description="Distanza dal parco più vicino (m)")
    bike_path_meters: Optional[float] = Field(None, description="Distanza dalla pista ciclabile più vicina (m)")

class FeaturesNearby(BaseModel):
    has_unibo: bool = Field(False, description="Presenza di sedi Unibo nel raggio")
    has_library: bool = Field(False, description="Presenza di biblioteche nel raggio")
    has_bus_stop: bool = Field(False, description="Presenza di fermate bus nel raggio")
    has_bike_rack: bool = Field(False, description="Presenza di rastrelliere nel raggio")
    has_green_area: bool = Field(False, description="Presenza di aree verdi nel raggio")
    has_bike_path: bool = Field(False, description="Presenza di piste ciclabili nel raggio")

class ContextSummaryResponse(BaseModel):
    coordinates: PointCoordinates
    radius_meters: int
    services_count: ServicesCount
    closest_distances_meters: ClosestDistances
    features_nearby: FeaturesNearby
    summary_text: str = Field(..., description="Sintesi qualitativa del contesto dell'area")

class ScoreWeights(BaseModel):
    study: float = Field(40.0, ge=0, le=100, description="Peso attribuito a studio e aule (default: 40)")
    transit: float = Field(30.0, ge=0, le=100, description="Peso attribuito al trasporto pubblico TPER (default: 30)")
    bike: float = Field(20.0, ge=0, le=100, description="Peso attribuito a ciclabilità e rastrelliere (default: 20)")
    green: float = Field(10.0, ge=0, le=100, description="Peso attribuito ad aree verdi e parchi (default: 10)")

class SubScores(BaseModel):
    study: float = Field(..., description="Sub-score per lo studio (0-100)")
    transit: float = Field(..., description="Sub-score per il trasporto pubblico (0-100)")
    bike: float = Field(..., description="Sub-score per la ciclabilità (0-100)")
    green: float = Field(..., description="Sub-score per le aree verdi (0-100)")

class TemporalContext(BaseModel):
    hour: int = Field(..., description="Ora considerata (0-23)")
    scenario: str = Field(..., description="Scenario temporale ('Diurno', 'Serale', 'Notturno')")
    is_night: bool = Field(..., description="Indica se l'orario ricade in fascia notturna")
    facilities_open_status: str = Field(..., description="Stato operativo delle strutture nell'orario")

class ScoreEvaluationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitudine")
    lon: float = Field(..., ge=-180, le=180, description="Longitudine")
    radius: int = Field(500, ge=50, le=5000, description="Raggio in metri")
    weights: Optional[ScoreWeights] = None
    hour: Optional[int] = Field(None, ge=0, le=23, description="Ora personalizzata (0-23) o orario corrente")

class ScoreEvaluationResponse(BaseModel):
    coordinates: PointCoordinates
    radius_meters: int
    total_score: float = Field(..., description="Student Accessibility Score complessivo (0-100)")
    rating_tier: str = Field(..., description="Livello qualitativo (es. Eccellente, Buono, Basso)")
    rating_color: str = Field(..., description="Codice colore esadecimale per UI")
    sub_scores: SubScores
    applied_weights: ScoreWeights
    temporal_context: TemporalContext
    strengths: List[str] = Field(..., description="Punti di forza dell'area")
    tradeoffs: List[str] = Field(..., description="Punti critici o trade-off dell'area")
    recommendation_text: str = Field(..., description="Raccomandazione contestuale personalizzata")


