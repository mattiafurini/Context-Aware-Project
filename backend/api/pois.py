from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/")
def get_pois_root():
    return {"message": "Endpoint POIs attivo"}
