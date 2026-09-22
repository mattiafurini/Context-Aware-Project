# Student Urban Accessibility Advisor 🎓🗺️

## Descrizione del Progetto
Questa piattaforma *context-aware* è sviluppata per supportare gli studenti universitari della città di Bologna. Il sistema analizza l'accessibilità urbana e fornisce raccomandazioni personalizzate sulle aree migliori in cui studiare o spostarsi, basandosi su fattori contestuali (orari, posizione) e sulle preferenze specifiche dell'utente (vicinanza a biblioteche, trasporto pubblico, aree verdi, piste ciclabili).

Il progetto è strutturato su un'architettura a microservizi e sfrutta la potenza del calcolo geospaziale nativo per processare enormi quantità di dati urbani.

## Struttura della Repository

Il codice è organizzato in tre livelli logici principali, ciascuno containerizzato in modo indipendente:

```text
student-urban-advisor/
├── backend/            # Logic Layer (Python / FastAPI)
│   ├── api/            # Endpoint RESTful (query spaziali, ranking, recommendation)
│   └── ...             # Script di data ingestion (Open Data & GTFS)
│
├── frontend/           # UI/UX Layer (Dashboard Web)
│   ├── index.html      # Struttura della dashboard
│   └── app.js          # Logica applicativa e rendering mappa tramite Leaflet.js
│
├── database/           # Data Layer (PostgreSQL + PostGIS)
│   └── init-scripts/   # Script SQL di autoconfigurazione eseguiti al primo avvio
│
├── data/               # Cartella locale (NON versionata) per i dataset
│   ├── raw/            # Dataset grezzi (GeoJSON, GTFS ZIP) scaricati dai portali
│   └── processed/      # Dataset ripuliti e pronti per l'ingestion nel DB
│
└── docker-compose.yml  # File di orchestrazione per avviare l'intera infrastruttura
```

## Tecnologie Principali
*   **DBMS:** PostgreSQL con estensione spaziale **PostGIS** (gestione indici R-Tree e query topologiche).
*   **Backend:** **Python 3** con **FastAPI** (alte prestazioni, parsing asincrono).
*   **Frontend:** HTML5, CSS3, JavaScript Vanilla e **Leaflet.js** per il Web Mapping.
*   **Data Science & GIS:** GeoPandas, SQLAlchemy/GeoAlchemy2.
*   **Infrastruttura:** Docker e Docker Compose.

## Fonti Dati (Open Data)
Il sistema aggrega ed elabora dati reali provenienti da:
1.  **Open Data Comune di Bologna:** Sedi universitarie, biblioteche, sale studio, mense, aree verdi, ciclabili.
2.  **TPER (Trasporto Passeggeri Emilia-Romagna):** Feed GTFS per l'analisi della rete di trasporto pubblico.

## Stato dello Sviluppo (Fase 1 Completata)
La **Fase 1 (Setup Infrastruttura e Data Ingestion)** è stata completata con successo. Attualmente il progetto dispone di:
- Una solida architettura a microservizi tramite `docker-compose`.
- Un database spaziale **PostGIS** inizializzato con uno schema relazionale ottimizzato (4 tabelle principali: `pois`, `aree_verdi`, `piste_ciclabili`, `fermate_tper`) e indici spaziali (R-Tree / GIST).
- Uno script Python di **Data Ingestion** (`backend/scripts_ingestion/ingest.py`) che standardizza tutte le coordinate al formato GPS (SRID 4326 WGS84) e popola massivamente il database convertendo i dati in formato binario spaziale (EWKB).

## Come avviare il progetto

1. **Avvio dell'infrastruttura Docker:**
   Nel terminale, lancia il seguente comando per creare e avviare i container (Database, Backend API, Frontend Web):
   ```bash
   docker compose up -d
   ```
   *Nota: Il database Postgres è mappato sulla porta `5433` verso l'host locale per evitare conflitti con eventuali installazioni Postgres pre-esistenti.*

2. **Esecuzione del Data Ingestion (Popolamento Database):**
   Una volta che i container sono in esecuzione, lancia lo script Python all'interno del container di backend per leggere i file grezzi in `data/raw`, pulirli e caricarli su PostGIS:
   ```bash
   docker exec -it urban_backend python scripts_ingestion/ingest.py
   ```
   Questo popolerà il database con sedi universitarie, biblioteche, rastrelliere, parchi, ciclabili e le fermate del trasporto pubblico (GTFS).
