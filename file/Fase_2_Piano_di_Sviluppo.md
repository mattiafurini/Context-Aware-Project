# Fase 2: Piano di Sviluppo (Backend Core & Spatial API) 🗺️⚡

Questo documento traccia i passaggi dettagliati per completare la **Fase 2** del progetto *Student Urban Accessibility Advisor*.  
L'obiettivo è trasformare il backend FastAPI in un motore di interrogazione geospaziale performante, sfruttando il calcolo nativo di **PostGIS** e gli indici spaziali GIST.

---

## 📋 Checklist di Avanzamento

- [x] **Step 1: Struttura Backend & Configurazione Database** ✅
  - [x] Creazione del modulo di connessione e sessioni SQLAlchemy (`backend/database.py`)
  - [x] Configurazione middleware CORS in `backend/main.py` per abilitare le chiamate dal frontend
  - [x] Predisposizione della cartella `backend/api/` con router modulari (`APIRouter`)

- [x] **Step 2: Endpoint Spaziali Core (Interrogazione del Territorio)** ✅
  - [x] `GET /api/pois/nearby`: ricerca PoI (università, biblioteche, rastrelliere) entro un raggio con distanza
  - [x] `GET /api/mobility/stops/nearby`: ricerca fermate TPER con raggio e distanza
  - [x] `GET /api/mobility/bikepaths`: esportazione tracciati piste ciclabili in formato GeoJSON
  - [x] `GET /api/green/areas`: esportazione parchi e aree verdi in formato GeoJSON

- [x] **Step 3: Endpoint di Analisi Contestuale (Context & Density)** ✅
  - [x] `GET /api/context/summary`: aggregazione statistica dei servizi entro un raggio da un punto GPS
  - [x] Validazione di supporto per il motore di raccomandazione della Fase 4

- [ ] **Step 4: Collaudo, Testing e Documentazione Swagger**
  - [ ] Verifica del corretto avvio nei container Docker (`docker compose up`)
  - [ ] Test interattivo delle route tramite Swagger UI (`http://localhost:8000/docs`)
  - [ ] Validazione delle performance e dell'uso degli indici GIST

---

## 🛠️ Dettaglio Operativo dei Passaggi

### Step 1: Struttura Backend & Connessione Database
1. **Connessione PostGIS (`backend/database.py`):**
   * Configurazione dell'`engine` SQLAlchemy tramite variabili d'ambiente (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
   * Creazione della session factory `SessionLocal = sessionmaker(...)`.
   * Definizione della dependency FastAPI `get_db()` con gestione automatica di chiusura connessione (`yield db`).
2. **Setup CORS (`backend/main.py`):**
   * Aggiunta del middleware `CORSMiddleware` consentendo le origini del frontend (`http://localhost:8080`, `http://127.0.0.1:8080`).
3. **Routing Modulare (`backend/api/`):**
   * Inclusione dei router in `main.py`:
     * `backend/api/pois.py`
     * `backend/api/mobility.py`
     * `backend/api/green.py`
     * `backend/api/context.py`

---

### Step 2: Endpoint Spaziali Core

#### 1. Ricerca PoI per Raggio (`GET /api/pois/nearby`)
* **Parametri Query:**
  * `lat` (float, obbligatorio): latitudine (es. `44.4965`)
  * `lon` (float, obbligatorio): longitudine (es. `11.3533`)
  * `radius` (int, default: `500`): raggio di ricerca in metri
  * `categoria` (string, opzionale): filtro categoria (`unibo`, `biblioteca`, `rastrelliera`, `museo`)
* **Logica PostGIS:**
  ```sql
  SELECT 
      id, nome, categoria, indirizzo,
      ST_Y(geom) AS lat, ST_X(geom) AS lon,
      ROUND(ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 1) AS distance_meters
  FROM pois
  WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
  ORDER BY distance_meters ASC;
  ```

#### 2. Fermate Autobus TPER Vicine (`GET /api/mobility/stops/nearby`)
* **Parametri Query:**
  * `lat`, `lon` (float, obbligatori)
  * `radius` (int, default: `400` metri)
* **Logica PostGIS:**
  * Interrogazione tabella `fermate_tper` con `ST_DWithin` geodetico e calcolo distanza in metri.

#### 3. Piste Ciclabili in GeoJSON (`GET /api/mobility/bikepaths`)
* **Parametri Query:**
  * `bbox` (opzionale): `min_lon,min_lat,max_lon,max_lat` per caricamento dinamico della vista mappa, oppure intero dataset per la città.
* **Logica PostGIS:**
  * Generazione diretta di GeoJSON tramite `ST_AsGeoJSON(geom)` restituito come `FeatureCollection` compatibile con Leaflet:
  ```sql
  SELECT json_build_object(
      'type', 'FeatureCollection',
      'features', json_agg(ST_AsGeoJSON(t.*)::json)
  ) FROM (
      SELECT id, tipologia, geom FROM piste_ciclabili
  ) t;
  ```

#### 4. Aree Verdi in GeoJSON (`GET /api/green/areas`)
* **Parametri Query:**
  * `bbox` o lista completa delle aree e toponimi verdi cittadini.
* **Logica PostGIS:**
  * Generazione di GeoJSON tramite `ST_AsGeoJSON(geom)`.

---

### Step 3: Endpoint di Analisi Contestuale (Context & Density)

#### `GET /api/context/summary`
* **Scopo:** Fornire un quadro istantaneo dei servizi e della vivibilità studentesca di una coordinata, essenziale per il calcolo dello score nella Fase 4.
* **Parametri Query:**
  * `lat`, `lon` (float, obbligatori)
  * `radius` (int, default: `500` metri)
* **Esempio Risposta:**
  ```json
  {
    "coordinates": {"lat": 44.4965, "lon": 11.3533},
    "radius_meters": 500,
    "services_count": {
      "unibo_locations": 4,
      "libraries": 2,
      "bus_stops": 7,
      "bike_racks": 6
    },
    "features_nearby": {
      "has_green_area": true,
      "has_bike_path": true
    }
  }
  ```

---

### Step 4: Collaudo e Coordinate di Test a Bologna

Per verificare gli endpoint su Swagger UI (`http://localhost:8000/docs`):

| Luogo di Test | Latitudine | Longitudine | Note |
| :--- | :--- | :--- | :--- |
| **Zona Universitaria (Via Zamboni / Piazza Scaravilli)** | `44.4965` | `11.3533` | Alta densità di aule, biblioteche e fermate |
| **Piazza Maggiore** | `44.4938` | `11.3426` | Centro storico, collegamenti TPER |
| **Giardini Margherita** | `44.4820` | `11.3530` | Alta presenza di aree verdi |
| **Stazione Centrale** | `44.5058` | `11.3430` | Snodo principale di mobilità |
