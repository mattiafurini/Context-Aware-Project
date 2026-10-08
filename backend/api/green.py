from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/")
def get_green_root():
    return {"message": "Endpoint Aree Verdi attivo"}
