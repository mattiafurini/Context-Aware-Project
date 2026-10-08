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
