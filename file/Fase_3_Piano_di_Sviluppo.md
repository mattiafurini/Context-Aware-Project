# Fase 3: Piano di Sviluppo (Frontend Dashboard & Web Mapping con Leaflet.js) 🗺️🎨

Questo documento traccia i passaggi dettagliati per completare la **Fase 3** del progetto *Student Urban Accessibility Advisor*.  
L'obiettivo è realizzare una dashboard web moderna, reattiva e interattiva, che integri la mappa con **Leaflet.js**, interroghi asincronamente il backend FastAPI e permetta allo studente di esplorare visivamente la città e i servizi universitari.

---

## 📋 Checklist di Avanzamento

- [x] **Step 1: Struttura UI & Design System Premium (`index.html` e `style.css`)** ✅
  - [x] Layout responsive con sidebar dei controlli/analytics e viewport mappa a tutto schermo
  - [x] Integrazione CDN Leaflet 1.9.4 e Google Fonts (*Outfit* / *Plus Jakarta Sans*) per un'estetica moderna e curata
  - [x] Foglio di stile `style.css` con variabili CSS, design contemporaneo (glassmorphism, dark/light mode elegante, micro-transizioni)
  - [x] Header con badge di stato connessione API (online/offline via `/api/health`)

- [x] **Step 2: Inizializzazione Mappa Leaflet & Caricamento Layer Multipli (`app.js`)** ✅
  - [x] Inizializzazione mappa centrata su Bologna (`[44.4949, 11.3426]`, zoom 15) con basemap pulita (*Esri Dark Gray Canvas*)
  - [x] Creazione dei `LayerGroup` controllabili per ogni servizio:
    - Layer POI universitari (icone e colori dedicati per Sedi Unibo, Biblioteche, Rastrelliere)
    - Layer Fermate TPER (icone bus e fermate)
    - Layer Piste Ciclabili (rendering vettoriale GeoJSON da `/api/mobility/bikepaths`)
    - Layer Aree Verdi (poligoni GeoJSON verdi traslucidi da `/api/green/areas`)
  - [x] Controllore dei layer e toggle interattivi

- [x] **Step 3: Interazione Spaziale, Click-on-Map & Buffer Circolare** ✅
  - [x] Listener al click sulla mappa: posizionamento marker "Posizione Studente" (draggabile)
  - [x] Disegno visivo della "Catchment Area" con cerchio di prossimità (`L.circle`) che riflette il raggio impostato
  - [x] Slider per regolare dinamicamente il raggio di analisi (da 200m a 1500m) con ridisegno in tempo reale del buffer circolare
  - [x] Tasti di scelta rapida per le coordinate chiave (Piazza Maggiore, Via Zamboni, Giardini Margherita, Stazione)

- [x] **Step 4: Card Contestuale & Live Analytics** ✅
  - [x] Chiamata asincrona `fetch()` a `GET /api/context/summary` al click o al cambio raggio
  - [x] Aggiornamento dinamico della sidebar con card statistiche:
    - Badge numerici dei servizi trovati (sedi, biblioteche, fermate, parchi, ciclabili)
    - Indicatori delle distanze minime a piedi (in metri)
    - Box con la sintesi contestuale generata dal backend
  - [x] Popup informativi ricchi al click sui marker (nome, categoria, indirizzo, distanza calcolata)

- [x] **Step 5: Predisposizione Slider Preferenze Utente (Ponte per la Fase 4)** ✅
  - [x] Slider percentuali per la profilazione utente:
    - 📚 Importanza Biblioteche & Aule Studio
    - 🚌 Importanza Trasporto Pubblico TPER
    - 🚲 Importanza Piste Ciclabili & Rastrelliere
    - 🌳 Importanza Aree Verdi & Parchi
  - [x] Box segnaposto per lo *Student Accessibility Score* (calcolato nella Fase 4)

---

## 🛠️ Dettaglio Architetturale dei File Coinvolti

```text
frontend/
├── Dockerfile          # Nginx Alpine (porta 8080)
├── index.html          # Struttura HTML5 semantica, sidebar controlli, container #map
├── style.css           # Design tokens, palette curata, layout flex/grid, card statistiche
└── app.js              # Inizializzazione Leaflet, logica di fetch API e gestione layer
```

---

## 🎨 Specifiche di Design e UX

1. **Palette Cromatica Distintiva per i Servizi:**
   * 🏛️ **Sedi Unibo / Aule Studio:** Rosso Accademico (`#b30000` / `#d9383a`)
   * 📚 **Biblioteche Comunali:** Blu Zaffiro (`#1d4ed8` / `#3b82f6`)
   * 🚌 **Fermate TPER:** Giallo/Ambra Bus (`#f59e0b` / `#d97706`)
   * 🚲 **Piste Ciclabili / Rastrelliere:** Turchese / Ciano (`#06b6d4` / `#0891b2`)
   * 🌳 **Aree Verdi / Parchi:** Smeraldo Naturale (`#10b981` / `#059669`)

2. **Feedback Visivo Immediato:**
   * Al click sulla mappa, l'utente vede il marker animarsi e il raggio di prossimità illuminarsi, con aggiornamento istantaneo del pannello laterale senza ricaricare la pagina.
