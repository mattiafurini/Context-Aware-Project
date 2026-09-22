Per completare la Fase 1, dovremmo affrontare tre macro-attività principali, operando in modo metodico. Dato che per ora non scriveremo codice, ti spiego il piano d'azione concettuale per questa fase:

- [x] ✅ **1. Strutturazione del Progetto e Setup Docker**
  Prima di tutto, dobbiamo creare lo "scheletro" del nostro progetto. L'obiettivo è avere un ambiente che parta con un solo comando (es. docker-compose up). Dovremo:
  * **Creare le cartelle principali:** Ad esempio backend/, frontend/, database/ e data/ (dove salveremo i file grezzi).
  * **Definire il docker-compose.yml:** Qui dichiareremo i nostri 3 container:
    * **Container DB:** Useremo un'immagine ufficiale di PostGIS (es. postgis/postgis). Configureremo anche un volume in modo che se spegniamo il container, non perdiamo tutti i dati spaziali caricati.
    * **Container Backend:** Un'immagine Python snella, in cui installeremo le librerie per FastAPI e per la gestione dati (es. geopandas, SQLAlchemy).
    * **Container Frontend:** Un'immagine leggerissima (come Nginx) che si limiterà a "servire" i nostri file HTML e Javascript di Leaflet al browser.

- [x] ✅ **2. Ricerca e Download dei Dati**
  Dobbiamo procurarci la "materia prima". Definiremo quali dati ci servono e li scaricheremo fisicamente nella cartella data/:
  * **Open Data Bologna:** Andremo sul portale Open Data del Comune di Bologna e cercheremo i dataset chiave in formato GeoJSON o Shapefile (sedi universitarie, biblioteche, sale studio, mense, aree verdi, piste ciclabili).
  * **Dati TPER (GTFS):** Cercheremo il feed pubblico GTFS di TPER (il formato standard internazionale per i trasporti pubblici) che contiene l'elenco delle fermate, i percorsi e gli orari.

- [ ] **3. Data Ingestion (Pulizia e Importazione Massiva)**
  Questa è la parte più critica della Fase 1. Prevede tre passaggi chiave gestiti da uno script Python:
  
  * **Definizione dello Schema (4 Tabelle principali in PostGIS):**
    * `pois`: Conterrà geometrie di tipo `Point` (coordinate esatte). Ospiterà le sedi universitarie, le biblioteche (dal file `mappe.csv`), sale studio e rastrelliere. Colonne principali: `id`, `nome`, `categoria`, `geom`.
    * `aree_verdi`: Conterrà geometrie di tipo `Polygon`. Ospiterà i parchi cittadini. Colonne principali: `id`, `nome`, `geom`.
    * `piste_ciclabili`: Conterrà geometrie di tipo `LineString`. Ospiterà i tracciati e percorsi ciclabili. Colonne principali: `id`, `tipologia`, `geom`.
    * `fermate_tper`: Conterrà geometrie di tipo `Point`. Ospiterà le fermate fisiche estratte dal feed GTFS (file `stops.txt`). Colonne principali: `id_fermata`, `nome_fermata`, `geom`.

  * **Pre-processing (Pulizia):**
    * **Standardizzazione Coordinate:** Tutte le coordinate dei file GeoJSON e CSV verranno proiettate o forzate nel sistema **SRID 4326** (WGS 84, il classico formato Lat/Lon del GPS) per essere compatibili con le mappe web (Leaflet).
    * **Pulizia:** Lo script leggerà riga per riga tramite Pandas, scartando i record con valori mancanti o coordinate corrotte per evitare crash sul database.
    * **Estrazione mirata:** Dal GTFS verranno prese solo le coordinate delle fermate; dal file `mappe.csv` di Unibo verranno estrapolati i dipartimenti e i luoghi di interesse, fondendo latitudine e longitudine in un punto spaziale.

  * **Popolamento del DB:**
    * **Ponte Python-PostGIS:** Lo script utilizzerà `SQLAlchemy` e `GeoAlchemy2` per convertire i dati puliti in comandi SQL ed eseguire un *Bulk Insert* veloce.
    * **Conversione Binaria:** Durante l'inserimento, le coordinate verranno tradotte nel formato binario compresso **EWKB** (Extended Well-Known Binary), ottimizzato per il calcolo spaziale.
    * **Creazione Indice Spaziale (Cruciale):** Subito dopo il caricamento, lo script ordinerà al database di creare un indice di tipo **GIST (R-Tree)** sulle colonne geometriche. Questo trasformerà le ricerche spaziali (es. "trova i servizi a 500m") da una lenta scansione sequenziale a un'operazione istantanea di pochi millisecondi.

Quando avremo completato questi tre passaggi, avremo un database funzionante, super ottimizzato, e pieno di dati reali, pronto per essere interrogato dalle API del backend.