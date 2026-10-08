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

