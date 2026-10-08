-- 01_init.sql
-- Script di inizializzazione del database per lo Student Urban Accessibility Advisor

-- 1. Abilitiamo il "superpotere" spaziale di PostgreSQL
CREATE EXTENSION IF NOT EXISTS postgis;

-- ==========================================
-- DEFINIZIONE DELLE TABELLE (SCHEMA)
-- ==========================================

-- Tabella 1: Punti di Interesse (Sedi Unibo, Biblioteche, Sale studio, Rastrelliere)
CREATE TABLE IF NOT EXISTS pois (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria TEXT,
    indirizzo TEXT,
    -- Geometria: PUNTO nel sistema di coordinate GPS standard (4326)
    geom GEOMETRY(Point, 4326)
);

-- Tabella 2: Aree Verdi (Parchi, Giardini)
CREATE TABLE IF NOT EXISTS aree_verdi (
    id SERIAL PRIMARY KEY,
    nome TEXT,
    -- Geometria: GEOMETRY (può essere Punto per i toponimi o MultiPoligono per le aree)
    geom GEOMETRY(Geometry, 4326)
);

-- Tabella 3: Piste Ciclabili (Percorsi e tracciati)
CREATE TABLE IF NOT EXISTS piste_ciclabili (
    id SERIAL PRIMARY KEY,
    tipologia TEXT,
    -- Geometria: MULTILINEA (una pista ciclabile può essere spezzata in più tratti)
    geom GEOMETRY(MultiLineString, 4326)
);

-- Tabella 4: Fermate Autobus (Dal feed GTFS di TPER)
CREATE TABLE IF NOT EXISTS fermate_tper (
    id_fermata VARCHAR(50) PRIMARY KEY,
    nome_fermata TEXT,
    -- Geometria: PUNTO
    geom GEOMETRY(Point, 4326)
);

-- ==========================================
-- CREAZIONE DEGLI INDICI SPAZIALI (GIST)
-- ==========================================
-- Questi indici sono fondamentali per velocizzare le query geografiche.
-- Senza questi, il calcolo della distanza tra te e una biblioteca richiederebbe un'eternità.

CREATE INDEX idx_pois_geom ON pois USING GIST (geom);
CREATE INDEX idx_aree_verdi_geom ON aree_verdi USING GIST (geom);
CREATE INDEX idx_piste_ciclabili_geom ON piste_ciclabili USING GIST (geom);
CREATE INDEX idx_fermate_tper_geom ON fermate_tper USING GIST (geom);

-- Indici spaziali funzionali GEOGRAPHY per query geodetiche in metri (ST_DWithin e ST_Distance)
CREATE INDEX idx_pois_geog ON pois USING GIST ((geom::geography));
CREATE INDEX idx_aree_verdi_geog ON aree_verdi USING GIST ((geom::geography));
CREATE INDEX idx_piste_ciclabili_geog ON piste_ciclabili USING GIST ((geom::geography));
CREATE INDEX idx_fermate_tper_geog ON fermate_tper USING GIST ((geom::geography));

