import os
import zipfile
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from geoalchemy2 import Geometry, WKTElement
from shapely.geometry import Point

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
# Usiamo le variabili d'ambiente per sicurezza, con valori di default per lo sviluppo locale
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "urban_accessibility")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# La cartella 'data/raw' si trova due livelli sopra rispetto a questo script se lo lanciamo da qui
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')

def get_file_path(filename):
    return os.path.join(DATA_DIR, filename)

# ==========================================
# FUNZIONI DI INGESTION
# ==========================================

def ingest_pois():
    print("Inizio ingestion POIs...")
    pois_list = []

    # 1. Unibo e Musei (dal CSV)
    try:
        path = get_file_path("mappe-unibo.csv")
        if os.path.exists(path):
            df_unibo = pd.read_csv(path)
            # Filtriamo per città Bologna ed escludiamo righe con coordinate assenti
            df_unibo = df_unibo[(df_unibo['city'].str.lower() == 'bologna') & (df_unibo['lat'].notnull()) & (df_unibo['lon'].notnull())]
            
            # Creazione geometria spaziale Point
            geometry = [Point(xy) for xy in zip(df_unibo['lon'], df_unibo['lat'])]
            gdf_unibo = gpd.GeoDataFrame(df_unibo, geometry=geometry, crs="EPSG:4326")
            
            # Uniformiamo le colonne per il DB
            gdf_unibo['categoria'] = gdf_unibo['type'].apply(lambda x: 'museo' if str(x).lower() == 'museo' else 'unibo')
            gdf_unibo = gdf_unibo[['name', 'categoria', 'address', 'geometry']]
            gdf_unibo.columns = ['nome', 'categoria', 'indirizzo', 'geom']
            pois_list.append(gdf_unibo)
            print(f" -> Letti {len(gdf_unibo)} record da mappe-unibo.csv")
    except Exception as e:
        print(f" -> ERRORE caricamento mappe-unibo.csv: {e}")

    # 2. Biblioteche (dal GeoJSON)
    try:
        path = get_file_path("biblioteche-comunali-di-bologna.geojson")
        if os.path.exists(path):
            gdf_biblio = gpd.read_file(path)
            # Forziamo a SRID 4326
            if gdf_biblio.crs != "EPSG:4326":
                gdf_biblio = gdf_biblio.to_crs("EPSG:4326")
                
            # Cerchiamo la colonna del nome (solitamente si chiama 'denominazione' o è la prima)
            nome_col = 'denominazione' if 'denominazione' in gdf_biblio.columns else gdf_biblio.columns[0]
            gdf_biblio['nome'] = gdf_biblio[nome_col]
            gdf_biblio['categoria'] = 'biblioteca'
            gdf_biblio['indirizzo'] = None # Potremmo estrarlo se presente, per ora lo lasciamo vuoto
            
            gdf_biblio = gdf_biblio[['nome', 'categoria', 'indirizzo', 'geometry']]
            gdf_biblio.columns = ['nome', 'categoria', 'indirizzo', 'geom']
            pois_list.append(gdf_biblio)
            print(f" -> Letti {len(gdf_biblio)} record da biblioteche")
    except Exception as e:
        print(f" -> ERRORE caricamento biblioteche: {e}")

    # 3. Rastrelliere (dal GeoJSON)
    try:
        path = get_file_path("rastrelliere-per-biciclette.geojson")
        if os.path.exists(path):
            gdf_rastrelliere = gpd.read_file(path)
            if gdf_rastrelliere.crs != "EPSG:4326":
                gdf_rastrelliere = gdf_rastrelliere.to_crs("EPSG:4326")
                
            gdf_rastrelliere['nome'] = 'Rastrelliera'
            gdf_rastrelliere['categoria'] = 'rastrelliera'
            gdf_rastrelliere['indirizzo'] = None
            
            gdf_rastrelliere = gdf_rastrelliere[['nome', 'categoria', 'indirizzo', 'geometry']]
            gdf_rastrelliere.columns = ['nome', 'categoria', 'indirizzo', 'geom']
            pois_list.append(gdf_rastrelliere)
            print(f" -> Letti {len(gdf_rastrelliere)} record da rastrelliere")
    except Exception as e:
        print(f" -> ERRORE caricamento rastrelliere: {e}")

    # Eseguiamo l'inserimento effettivo nel database
    if pois_list:
        final_gdf = pd.concat(pois_list, ignore_index=True)
        final_gdf = final_gdf[final_gdf['geom'].notnull()] # Rimuove nulli finali
        
        # Alcuni GeoJSON (es. rastrelliere) usano MultiPoint invece di Point.
        # Li forziamo a Point prendendo la prima coordinata.
        final_gdf['geom'] = final_gdf['geom'].apply(
            lambda g: g.geoms[0] if g.geom_type == 'MultiPoint' else g
        )
        
        # Converte le geometrie di Shapely in WKTElement capiti da GeoAlchemy2
        final_gdf['geom'] = final_gdf['geom'].apply(lambda geom: WKTElement(geom.wkt, srid=4326))
        
        # Bulk insert
        final_gdf.to_sql('pois', engine, if_exists='append', index=False,
                         dtype={'geom': Geometry('POINT', srid=4326)})
        print(f"✅ Inseriti {len(final_gdf)} POIs in PostGIS.")
    else:
        print("Nessun POI trovato da inserire.")

def ingest_aree_verdi():
    print("\nInizio ingestion Aree Verdi...")
    try:
        path = get_file_path("carta-tecnica-comunale-toponimi-parchi-e-giardini.geojson")
        if not os.path.exists(path):
            return
            
        gdf = gpd.read_file(path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        
        gdf = gdf[gdf.geometry.notnull()]
        
        # Non forziamo più a MultiPolygon, perché i file toponimi contengono Punti
        if 'toponimo' in gdf.columns:
            nome_col = 'toponimo'
        elif 'nomevia' in gdf.columns:
            nome_col = 'nomevia'
        else:
            nome_col = None
            
        if nome_col:
            gdf['nome'] = gdf[nome_col]
        else:
            gdf['nome'] = 'Area Verde'
        
        gdf = gdf[['nome', 'geometry']]
        gdf.columns = ['nome', 'geom']

        gdf['geom'] = gdf['geom'].apply(lambda geom: WKTElement(geom.wkt, srid=4326))
        
        gdf.to_sql('aree_verdi', engine, if_exists='append', index=False,
                   dtype={'geom': Geometry('GEOMETRY', srid=4326)})
        print(f"✅ Inserite {len(gdf)} aree verdi in PostGIS.")
    except Exception as e:
        print(f" -> ERRORE caricamento aree verdi: {e}")

def ingest_piste_ciclabili():
    print("\nInizio ingestion Piste Ciclabili...")
    piste_list = []
    files = ["piste-ciclopedonali.geojson", "biciplan-il-piano-ciclistico-comunale.geojson"]
    
    for f in files:
        try:
            path = get_file_path(f)
            if not os.path.exists(path):
                continue
                
            gdf = gpd.read_file(path)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            
            gdf = gdf[gdf.geometry.notnull()]
            
            from shapely.geometry.multilinestring import MultiLineString
            gdf['geometry'] = gdf['geometry'].apply(
                lambda g: MultiLineString([g]) if g.geom_type == 'LineString' else g
            )
            
            gdf['tipologia'] = 'Pista ciclabile' if 'biciplan' not in f else 'Biciplan'
            
            gdf = gdf[['tipologia', 'geometry']]
            gdf.columns = ['tipologia', 'geom']
            piste_list.append(gdf)
            print(f" -> Letti {len(gdf)} record da {f}")
        except Exception as e:
            print(f" -> ERRORE caricamento {f}: {e}")
            
    if piste_list:
        final_gdf = pd.concat(piste_list, ignore_index=True)
        final_gdf['geom'] = final_gdf['geom'].apply(lambda geom: WKTElement(geom.wkt, srid=4326))
        
        final_gdf.to_sql('piste_ciclabili', engine, if_exists='append', index=False,
                         dtype={'geom': Geometry('MULTILINESTRING', srid=4326)})
        print(f"✅ Inserite {len(final_gdf)} piste ciclabili in PostGIS.")

def ingest_fermate_tper():
    print("\nInizio ingestion Fermate TPER (GTFS)...")
    try:
        zip_path = get_file_path("gommagtfsbo_20260709.zip")
        if not os.path.exists(zip_path):
            print(" -> File GTFS non trovato.")
            return
            
        with zipfile.ZipFile(zip_path, 'r') as z:
            with z.open('stops.txt') as f:
                df = pd.read_csv(f)
                
        # Filtro via fermate senza coordinate valide
        df = df[(df['stop_lat'].notnull()) & (df['stop_lon'].notnull())]
        
        # Creazione Point
        geometry = [Point(xy) for xy in zip(df['stop_lon'], df['stop_lat'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
        gdf = gdf[['stop_id', 'stop_name', 'geometry']]
        gdf.columns = ['id_fermata', 'nome_fermata', 'geom']
        
        gdf['geom'] = gdf['geom'].apply(lambda geom: WKTElement(geom.wkt, srid=4326))
        
        gdf.to_sql('fermate_tper', engine, if_exists='append', index=False,
                   dtype={'geom': Geometry('POINT', srid=4326)})
        print(f"✅ Inserite {len(gdf)} fermate TPER in PostGIS.")
    except Exception as e:
        print(f" -> ERRORE caricamento fermate TPER: {e}")

if __name__ == "__main__":
    print("==========================================")
    print(" AVVIO DATA INGESTION SCRIPT")
    print("==========================================\n")
    ingest_pois()
    ingest_aree_verdi()
    ingest_piste_ciclabili()
    ingest_fermate_tper()
    print("\n==========================================")
    print(" DATA INGESTION COMPLETATA!")
    print("==========================================")
