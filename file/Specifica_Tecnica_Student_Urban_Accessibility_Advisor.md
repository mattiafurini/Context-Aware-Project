# Specifica Tecnica e Piano di Sviluppo
## Proposta 4: Student Urban Accessibility Advisor

### 1. Obiettivi del Progetto
Il progetto mira a sviluppare una piattaforma "context-aware" rivolta agli studenti universitari della città di Bologna. L'obiettivo è analizzare l'accessibilità urbana e consigliare le aree migliori in base al contesto (orario, posizione) e alle preferenze personali dell'utente (es. vicinanza alle biblioteche, trasporto pubblico, mobilità sostenibile).
A differenza di soluzioni mobile-first, si adotterà un approccio web-based (Dashboard Web Interattiva), demandando la complessità computazionale e spaziale al database (PostGIS).

### 2. Architettura del Sistema
Il sistema adotterà un'architettura a microservizi, orchestrata tramite **Docker Compose**, suddivisa in tre livelli principali:
- **Data Layer (DBMS):** PostgreSQL con estensione spaziale PostGIS. Si occuperà dell'indicizzazione spaziale (R-Tree) e dell'esecuzione nativa delle interrogazioni topologiche (buffer, distanze, densità), garantendo alte performance per le Box Query.
- **Logic Layer (Backend):** Sviluppato in Python (FastAPI). Esporrà API RESTful per gestire la logica di business, l'ingestione dei dati (Open Data, GTFS) e il motore di raccomandazione context-aware.
- **UI/UX Layer (Frontend):** Dashboard Web interattiva realizzata in HTML/JS o framework leggero, integrata con librerie di Web Mapping come **Leaflet** o **OpenLayers** per la visualizzazione multilivello.

### 3. Modellazione Dati e Ingestion (PostGIS)
I dati saranno ricavati dagli Open Data del Comune di Bologna e dai feed GTFS di TPER.
Tipi di dato spaziali principali:
- **Point / Geography:** Sedi universitarie, biblioteche, mense, sale studio, fermate autobus. L'uso di `Geography` (SRID 4326) garantirà precisione geodetica per le query `ST_Distance` e `ST_DWithin`.
- **LineString:** Reti di piste ciclabili e percorsi autobus.
- **Polygon:** Aree verdi e parchi urbani.

**Fase di Ingestion:** I dataset grezzi saranno sottoposti a pre-processing e pulizia (Data Cleaning) all'avvio del sistema tramite script dedicati, prima dell'inserimento nel DB spaziale, per gestire valori nulli o incoerenze.

### 4. Applicativo Base (Core MVP)
- **Mappa Multilayer:** Visualizzazione su mappa dei punti di interesse (PoI).
- **Interrogazione Spaziale:** Possibilità per l'utente di cliccare su una zona o fornire una posizione per interrogare i servizi entro un raggio specificato tramite API RESTful.
- **Ranking Base:** Un sistema iniziale che valuta un'area in base a due fattori contestuali semplici (es. distanza dalla sede universitaria più vicina e disponibilità di fermate autobus nei dintorni).

### 5. Funzionalità Avanzate "30 e Lode" (Bonus)
Per massimizzare la valutazione, il sistema integrerà i seguenti moduli avanzati, rimuovendo le derive su sistemi "HAR / Parcheggi Auto" per concentrarsi sulla mobilità studentesca:
- **Profilazione e Dynamic Ranking:** L'utente potrà regolare tramite slider l'importanza dei vari servizi (es. 80% trasporti, 20% aree verdi). Il sistema calcolerà uno "Student Accessibility Score" dinamico basato su somme pesate.
- **Analisi Spaziale:** Uso di `ST_Buffer` per analizzare la "catchment area" dei servizi (es. area di copertura a 500m da una biblioteca) e generazione di heatmap per identificare zone di "deserto dei servizi".
- **Mobility Analytics & GTFS:** Integrazione dei feed TPER per calcolare isocrone temporali e valutare l'effettiva raggiungibilità delle sedi (trasporto pubblico vs walking/biking).
- **Recommendation Engine Context-Aware:** Il sistema non si limiterà a fornire un punteggio, ma aggiungerà una motivazione esplicita (es. *"Area altamente consigliata per l'alta densità di piste ciclabili e sale studio"*).
- **Temporal Analytics:** I dati verranno filtrati dinamicamente in base all'orario (es. mostrando solo sale studio o biblioteche attualmente aperte, analizzando scenari diurni vs notturni).
- **Privacy Location-Aware:** Prima dell'invio della posizione al backend, verrà applicata una tecnica di *spatial perturbation* (rumore casuale). Sarà visualizzato graficamente il trade-off tra l'accuratezza del suggerimento perso (Reducible Error) e il livello di privacy guadagnato.
- **Advanced Spatial Clustering:** Uso dell'algoritmo DBSCAN (lato Python o DB) per individuare automaticamente cluster e zone ad alta densità di servizi universitari.

### 6. Piano di Sviluppo (Work Breakdown Structure)
- **Fase 1 (Setup & Data Ingestion):** Configurazione container Docker (DB + Backend + Frontend), download, pulizia e importazione massiva degli Open Data e dati GTFS su PostGIS.
- **Fase 2 (Backend Core & Spatial API):** Sviluppo degli endpoint FastAPI per operazioni CRUD spaziali (`ST_DWithin`, indicizzazione R-Tree).
- **Fase 3 (Frontend Dashboard):** Implementazione di Leaflet, gestione asincrona dei layer su mappa e creazione dell'interfaccia a slider per le preferenze.
- **Fase 4 (Advanced Context & Recommendations):** Sviluppo del motore per il calcolo dello score dinamico, applicazione dei filtri temporali e generazione delle raccomandazioni testuali.
- **Fase 5 (Analytics, Clustering & Privacy):** Implementazione degli algoritmi DBSCAN, generazione automatica di isocrone/heatmap e finalizzazione del modulo di perturbazione per la privacy.
