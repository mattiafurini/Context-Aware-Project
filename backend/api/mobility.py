from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/")
def get_mobility_root():
    return {"message": "Endpoint Mobilità e Trasporti attivo"}
