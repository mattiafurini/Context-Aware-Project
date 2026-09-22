from fastapi import FastAPI

app = FastAPI(title="Student Urban Accessibility API")

@app.get("/")
def read_root():
    return {"message": "Backend FastAPI funzionante! Pronto per le query spaziali."}
