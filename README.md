# Student Urban Accessibility Advisor 🎓🗺️

## Descrizione del Progetto
Questa piattaforma *context-aware* è sviluppata per supportare gli studenti universitari della città di Bologna. Il sistema analizza l'accessibilità urbana e fornisce raccomandazioni personalizzate sulle aree migliori in cui studiare o spostarsi, basandosi su fattori contestuali (orari, posizione) e sulle preferenze specifiche dell'utente (vicinanza a biblioteche, trasporto pubblico, aree verdi, piste ciclabili).

Il progetto è strutturato su un'architettura a microservizi e sfrutta la potenza del calcolo geospaziale nativo di **PostGIS** per processare ed interrogare dati urbani complessi.

## Struttura della Repository

Il codice è organizzato in tre livelli logici principali, ciascuno containerizzato in modo indipendente:

```text
Context-Aware-Project/
├── backend/            # Logic Layer (Python / FastAPI)
│   ├── api/            # Router RESTful modulari (pois, mobility, green, context)
│   ├── database.py     # Connessione SQLAlchemy e gestione sessioni PostGIS
│   ├── main.py         # Entrypoint FastAPI con CORS e diagnostica
│   ├── scripts_ingestion/ # Script di data ingestion (Open Data & GTFS)
│   └── requirements.txt# Dipendenze Python
│
├── frontend/           # UI/UX Layer (Dashboard Web)
│   ├── index.html      # Struttura della dashboard
│   ├── style.css       # Fogli di stile
│   └── app.js          # Logica applicativa e rendering mappa tramite Leaflet.js
│
├── database/           # Data Layer (PostgreSQL + PostGIS)
│   └── init-scripts/   # Script SQL di autoconfigurazione eseguiti al primo avvio
│
├── data/               # Dataset urbani
│   ├── raw/            # Dataset grezzi (GeoJSON, GTFS ZIP, CSV)
│   └── processed/      # Dataset ripuliti e intermedi
│
├── file/               # Specifiche di progetto, piani di sviluppo e documentazione esame
│   └── Fase_2_Piano_di_Sviluppo.md # Piano operativo e checklist della Fase 2
│
└── docker-compose.yml  # Orchestrazione container Docker
```

## Tecnologie Principali
* **DBMS:** PostgreSQL con estensione spaziale **PostGIS** (gestione indici GIST / R-Tree e query topologiche native).
* **Backend:** **Python 3** con **FastAPI** (asincrono, documentazione OpenAPI / Swagger automatica).
* **Frontend:** HTML5, CSS3, JavaScript Vanilla e **Leaflet.js** per il Web Mapping.
* **Data Science & GIS:** GeoPandas, SQLAlchemy, GeoAlchemy2, Shapely.
* **Infrastruttura:** Docker e Docker Compose.

## Fonti Dati (Open Data)
Il sistema aggrega ed elabora dati reali provenienti da:
1. **Open Data Comune di Bologna & Unibo:** Sedi universitarie, biblioteche, sale studio, mense, aree verdi, piste ciclabili, rastrelliere.
2. **TPER (Trasporto Passeggeri Emilia-Romagna):** Feed GTFS per l'analisi della rete di trasporto pubblico su gomma.

## Stato dello Sviluppo

- **Fase 1 (Setup Infrastruttura e Data Ingestion) – Completata ✅**
  - Architettura a microservizi orchestrata con Docker Compose.
  - Schema PostGIS inizializzato con 4 tabelle principali (`pois`, `aree_verdi`, `piste_ciclabili`, `fermate_tper`) e relativi indici spaziali GIST.
  - Pipeline di Data Ingestion (`backend/scripts_ingestion/ingest.py`) che standardizza le coordinate a SRID 4326 (WGS84) ed esegue il caricamento massivo in formato binario spaziale EWKB.

- **Fase 2 (Backend Core & Spatial API) – In corso 🚀**
  - **Step 1 Completato ✅:**
    - Configurato il connection pool SQLAlchemy verso PostGIS con dependency injection (`backend/database.py`).
    - Configurato il middleware CORS in FastAPI per consentire l'interazione fluida con il frontend.
    - Strutturata l'architettura a router modulari in `backend/api/` (`pois.py`, `mobility.py`, `green.py`, `context.py`).
    - Implementato l'endpoint diagnostico `/api/health` per validare la connettività al database e l'estensione PostGIS.
    - Creato il piano di sviluppo dettagliato in [file/Fase_2_Piano_di_Sviluppo.md](file/Fase_2_Piano_di_Sviluppo.md).
  - **Step 2 (Prossimo Passo):** Implementazione degli endpoint geospaziali core (`ST_DWithin`, calcolo distanze in metri, esportazione GeoJSON).

## Come Avviare il Progetto

1. **Avvio dell'infrastruttura Docker:**
   Nel terminale, lancia il seguente comando per creare e avviare i container (Database, Backend API, Frontend Web):
   ```bash
   docker compose up -d
   ```
   *Nota: Il database Postgres è mappato sulla porta `5433` verso l'host locale per evitare conflitti con eventuali istanze Postgres pre-esistenti.*

2. **Esecuzione del Data Ingestion (Popolamento Database):**
   Una volta che i container sono attivi, lancia lo script di ingestion nel container di backend:
   ```bash
   docker exec -it urban_backend python scripts_ingestion/ingest.py
   ```

3. **Accesso ai Servizi:**
   * **Dashboard Frontend:** [http://localhost:8080](http://localhost:8080)
   * **Backend API Root:** [http://localhost:8000](http://localhost:8000)
   * **Documentazione Interattiva Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Documentazione Alternativa ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
   * **Verifica Stato Salute & PostGIS:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
