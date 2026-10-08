/**
 * Student Urban Accessibility Advisor - Bologna 🎓🗺️
 * Frontend Web Mapping & Analytics Controller (Leaflet.js)
 */

const API_BASE = "http://localhost:8000";

// Stato applicativo corrente
const state = {
    currentLat: 44.4965,
    currentLon: 11.3533,
    radius: 500,
    layers: {
        unibo: true,
        biblioteche: true,
        tper: true,
        ciclabili: true,
        verdi: true,
        rastrelliere: false
    },
    weights: {
        study: 40,
        transit: 30,
        bike: 20,
        green: 10
    },
    hour: 14
};

// Elementi DOM
const dom = {
    apiStatusBadge: document.getElementById("api-status-badge"),
    apiStatusText: document.getElementById("api-status-text"),
    btnToggleSidebar: document.getElementById("btn-toggle-sidebar"),
    sidebar: document.getElementById("sidebar"),
    radiusSlider: document.getElementById("radius-slider"),
    radiusValueBadge: document.getElementById("radius-value-badge"),
    coordsText: document.getElementById("coords-text"),
    chips: document.querySelectorAll(".chip"),
    // Contatori
    countUnibo: document.getElementById("count-unibo"),
    distUnibo: document.getElementById("dist-unibo"),
    countBiblio: document.getElementById("count-biblio"),
    distBiblio: document.getElementById("dist-biblio"),
    countBus: document.getElementById("count-bus"),
    distBus: document.getElementById("dist-bus"),
    countBici: document.getElementById("count-bici"),
    distBici: document.getElementById("dist-bici"),
    countVerde: document.getElementById("count-verde"),
    distVerde: document.getElementById("dist-verde"),
    countRacks: document.getElementById("count-racks"),
    distRacks: document.getElementById("dist-racks"),
    summaryText: document.getElementById("context-summary-text"),
    // Layer toggles
    toggleUnibo: document.getElementById("toggle-unibo"),
    toggleBiblio: document.getElementById("toggle-biblioteche"),
    toggleTper: document.getElementById("toggle-tper"),
    toggleCiclabili: document.getElementById("toggle-ciclabili"),
    toggleVerdi: document.getElementById("toggle-verdi"),
    toggleRacks: document.getElementById("toggle-rastrelliere"),
    // Slider preferenze
    weightStudy: document.getElementById("weight-study"),
    weightStudyVal: document.getElementById("weight-study-val"),
    weightTransit: document.getElementById("weight-transit"),
    weightTransitVal: document.getElementById("weight-transit-val"),
    weightBike: document.getElementById("weight-bike"),
    weightBikeVal: document.getElementById("weight-bike-val"),
    weightGreen: document.getElementById("weight-green"),
    weightGreenVal: document.getElementById("weight-green-val"),
    // Time Awareness
    timeChips: document.querySelectorAll(".time-chip"),
    facilityStatusText: document.getElementById("facility-status-text"),
    // Score & Recommendation
    scoreCircle: document.getElementById("score-circle"),
    scoreNumber: document.getElementById("score-number"),
    tierBadge: document.getElementById("tier-badge"),
    fillStudy: document.getElementById("fill-study"),
    valStudy: document.getElementById("val-study"),
    fillTransit: document.getElementById("fill-transit"),
    valTransit: document.getElementById("val-transit"),
    fillBike: document.getElementById("fill-bike"),
    valBike: document.getElementById("val-bike"),
    fillGreen: document.getElementById("fill-green"),
    valGreen: document.getElementById("val-green"),
    recParagraph: document.getElementById("rec-paragraph"),
    strengthsList: document.getElementById("strengths-list"),
    tradeoffsList: document.getElementById("tradeoffs-list")
};

// Inizializzazione Leaflet
let map;
let studentMarker;
let bufferCircle;

// Layer Groups
const layerGroups = {
    unibo: L.layerGroup(),
    biblioteche: L.layerGroup(),
    tper: L.layerGroup(),
    ciclabili: L.layerGroup(),
    verdi: L.layerGroup(),
    rastrelliere: L.layerGroup(),
    analysis: L.layerGroup()
};

/**
 * 1. Setup e Avvio della Mappa
 */
function initMap() {
    map = L.map("map", {
        center: [state.currentLat, state.currentLon],
        zoom: 15,
        zoomControl: false
    });

    // Zoom control in alto a destra
    L.control.zoom({ position: "topright" }).addTo(map);

    // Basemap scura Esri Dark Gray Canvas ad altissima leggibilità
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16
    }).addTo(map);

    // Layer etichette stradali per conservare la toponomastica
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
        attribution: '',
        maxZoom: 16
    }).addTo(map);

    // Aggiungiamo i layer attivi alla mappa
    Object.keys(layerGroups).forEach(key => {
        if (key === "analysis" || state.layers[key] !== false) {
            layerGroups[key].addTo(map);
        }
    });

    // Marker Studente e Buffer iniziale
    updateAnalysisMarker(state.currentLat, state.currentLon);

    // Event listener click su mappa
    map.on("click", (e) => {
        setNewLocation(e.latlng.lat, e.latlng.lng);
    });
}

/**
 * Crea icone HTML personalizzate per Leaflet
 */
function createCustomIcon(iconClass, color, size = 30) {
    return L.divIcon({
        className: "custom-leaflet-icon",
        html: `
            <div style="
                background: ${color};
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                box-shadow: 0 0 10px ${color}88, 0 2px 5px rgba(0,0,0,0.5);
                border: 2px solid white;
                font-size: ${size * 0.45}px;
            ">
                <i class="${iconClass}"></i>
            </div>
        `,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2]
    });
}

/**
 * 2. Posizionamento Marker Studente e Cerchio di Prossimità
 */
function updateAnalysisMarker(lat, lon) {
    layerGroups.analysis.clearLayers();

    // Marker con animazione pulsante
    const studentIcon = L.divIcon({
        className: "student-pulse-marker",
        html: `
            <div style="
                width: 36px;
                height: 36px;
                background: #6366f1;
                border: 3px solid white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 16px;
                box-shadow: 0 0 20px #6366f1;
                cursor: grab;
            ">
                <i class="fa-solid fa-person-walking"></i>
            </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
    });

    studentMarker = L.marker([lat, lon], {
        icon: studentIcon,
        draggable: true,
        title: "La tua posizione analizzata (trascina per spostare)"
    });

    studentMarker.on("dragend", (e) => {
        const pos = e.target.getLatLng();
        setNewLocation(pos.lat, pos.lng);
    });

    // Cerchio Buffer geodetico
    bufferCircle = L.circle([lat, lon], {
        radius: state.radius,
        color: "#6366f1",
        weight: 2,
        dashArray: "6, 6",
        fillColor: "#6366f1",
        fillOpacity: 0.12
    });

    layerGroups.analysis.addLayer(bufferCircle);
    layerGroups.analysis.addLayer(studentMarker);
}

/**
 * Aggiorna la posizione e ricarica i dati
 */
function setNewLocation(lat, lon) {
    state.currentLat = parseFloat(lat.toFixed(6));
    state.currentLon = parseFloat(lon.toFixed(6));

    dom.coordsText.textContent = `${state.currentLat.toFixed(5)}° N, ${state.currentLon.toFixed(5)}° E`;

    updateAnalysisMarker(state.currentLat, state.currentLon);
    refreshData();
}

/**
 * 3. Chiamate API al Backend FastAPI
 */
async function refreshData() {
    await Promise.all([
        fetchContextSummary(),
        fetchAccessibilityEvaluation(),
        fetchPoisNearby(),
        fetchStopsNearby()
    ]);
}

/**
 * Caricamento Statistiche Contestuali
 */
async function fetchContextSummary() {
    dom.summaryText.textContent = "Analisi topologica in corso...";
    try {
        const url = `${API_BASE}/api/context/summary?lat=${state.currentLat}&lon=${state.currentLon}&radius=${state.radius}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Errore API summary");
        const data = await res.json();

        // Aggiornamento conteggi
        const sc = data.services_count;
        const cd = data.closest_distances_meters;

        dom.countUnibo.textContent = sc.unibo_locations;
        dom.distUnibo.textContent = cd.unibo_meters ? `${cd.unibo_meters.toFixed(0)}m` : "assente";

        dom.countBiblio.textContent = sc.libraries;
        dom.distBiblio.textContent = cd.library_meters ? `${cd.library_meters.toFixed(0)}m` : "assente";

        dom.countBus.textContent = sc.bus_stops;
        dom.distBus.textContent = cd.bus_stop_meters ? `${cd.bus_stop_meters.toFixed(0)}m` : "assente";

        dom.countBici.textContent = sc.bike_paths;
        dom.distBici.textContent = cd.bike_path_meters ? `${cd.bike_path_meters.toFixed(0)}m` : "assente";

        dom.countVerde.textContent = sc.green_areas;
        dom.distVerde.textContent = cd.green_area_meters ? `${cd.green_area_meters.toFixed(0)}m` : "assente";

        dom.countRacks.textContent = sc.bike_racks;
        dom.distRacks.textContent = cd.bike_rack_meters ? `${cd.bike_rack_meters.toFixed(0)}m` : "assente";

        dom.summaryText.textContent = data.summary_text;
    } catch (e) {
        dom.summaryText.textContent = "Impossibile recuperare i dati contestuali. Verifica lo stato delle API.";
        console.error(e);
    }
}

/**
 * Calcolo Dinamico Accessibility Score e Raccomandazione (Fase 4)
 */
async function fetchAccessibilityEvaluation() {
    try {
        const hourParam = state.hour === "now" ? new Date().getHours() : state.hour;
        const url = `${API_BASE}/api/context/evaluate?lat=${state.currentLat}&lon=${state.currentLon}&radius=${state.radius}&weight_study=${state.weights.study}&weight_transit=${state.weights.transit}&weight_bike=${state.weights.bike}&weight_green=${state.weights.green}&hour=${hourParam}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Errore API evaluate");
        const data = await res.json();

        // 1. Punteggio Complessivo e Livello
        dom.scoreNumber.textContent = data.total_score.toFixed(1);
        dom.tierBadge.textContent = data.rating_tier;
        dom.tierBadge.style.color = data.rating_color;
        dom.tierBadge.style.borderColor = data.rating_color;
        dom.tierBadge.style.background = `${data.rating_color}22`;
        dom.scoreCircle.style.borderColor = data.rating_color;
        dom.scoreCircle.style.boxShadow = `0 0 20px ${data.rating_color}44`;

        // 2. Sub-Scores Breakdown
        dom.fillStudy.style.width = `${Math.min(100, Math.max(0, data.sub_scores.study))}%`;
        dom.valStudy.textContent = `${Math.round(data.sub_scores.study)}%`;

        dom.fillTransit.style.width = `${Math.min(100, Math.max(0, data.sub_scores.transit))}%`;
        dom.valTransit.textContent = `${Math.round(data.sub_scores.transit)}%`;

        dom.fillBike.style.width = `${Math.min(100, Math.max(0, data.sub_scores.bike))}%`;
        dom.valBike.textContent = `${Math.round(data.sub_scores.bike)}%`;

        dom.fillGreen.style.width = `${Math.min(100, Math.max(0, data.sub_scores.green))}%`;
        dom.valGreen.textContent = `${Math.round(data.sub_scores.green)}%`;

        // 3. Stato Operativo Strutture (Time-Awareness)
        dom.facilityStatusText.textContent = data.temporal_context.facilities_open_status;

        // 4. Raccomandazione Esplicita
        dom.recParagraph.textContent = data.recommendation_text;

        // 5. Punti di Forza
        dom.strengthsList.innerHTML = data.strengths.map(s => `<li>${s}</li>`).join("");

        // 6. Trade-Offs
        dom.tradeoffsList.innerHTML = data.tradeoffs.map(t => `<li>${t}</li>`).join("");
    } catch (e) {
        console.error("Errore fetch accessibility evaluation:", e);
    }
}


/**
 * Caricamento POIs vicini (Sedi Unibo, Biblioteche, Rastrelliere)
 */
async function fetchPoisNearby() {
    layerGroups.unibo.clearLayers();
    layerGroups.biblioteche.clearLayers();
    layerGroups.rastrelliere.clearLayers();

    try {
        const url = `${API_BASE}/api/pois/nearby?lat=${state.currentLat}&lon=${state.currentLon}&radius=${state.radius}&limit=200`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Errore API POIs");
        const data = await res.json();

        data.results.forEach(poi => {
            let icon, targetGroup, tagClass;

            if (poi.categoria === "biblioteca") {
                icon = createCustomIcon("fa-solid fa-book-open", "#3b82f6", 26);
                targetGroup = layerGroups.biblioteche;
                tagClass = "biblioteca";
            } else if (poi.categoria === "rastrelliera") {
                icon = createCustomIcon("fa-solid fa-square-parking", "#8b5cf6", 22);
                targetGroup = layerGroups.rastrelliere;
                tagClass = "racks";
            } else {
                icon = createCustomIcon("fa-solid fa-building-columns", "#e11d48", 26);
                targetGroup = layerGroups.unibo;
                tagClass = "unibo";
            }

            const marker = L.marker([poi.lat, poi.lon], { icon });
            marker.bindPopup(`
                <div class="popup-content">
                    <span class="popup-tag ${tagClass}">${poi.categoria.toUpperCase()}</span>
                    <h4>${poi.nome}</h4>
                    ${poi.indirizzo ? `<p class="popup-meta"><i class="fa-solid fa-location-dot"></i> ${poi.indirizzo}</p>` : ""}
                    <p class="popup-meta" style="margin-top: 4px; font-weight: 600; color: #6366f1;">
                        <i class="fa-solid fa-person-walking"></i> Distanza: ${poi.distance_meters.toFixed(0)} metri
                    </p>
                </div>
            `);

            targetGroup.addLayer(marker);
        });
    } catch (e) {
        console.error("Errore fetch POIs:", e);
    }
}

/**
 * Caricamento Fermate TPER vicine
 */
async function fetchStopsNearby() {
    layerGroups.tper.clearLayers();
    try {
        const url = `${API_BASE}/api/mobility/stops/nearby?lat=${state.currentLat}&lon=${state.currentLon}&radius=${state.radius}&limit=150`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Errore API fermate");
        const data = await res.json();

        const busIcon = createCustomIcon("fa-solid fa-bus", "#f59e0b", 22);

        data.results.forEach(stop => {
            const marker = L.marker([stop.lat, stop.lon], { icon: busIcon });
            marker.bindPopup(`
                <div class="popup-content">
                    <span class="popup-tag bus">FERMATA TPER</span>
                    <h4>${stop.nome_fermata}</h4>
                    <p class="popup-meta">ID Fermata: ${stop.id_fermata}</p>
                    <p class="popup-meta" style="margin-top: 4px; font-weight: 600; color: #f59e0b;">
                        <i class="fa-solid fa-person-walking"></i> Distanza: ${stop.distance_meters.toFixed(0)} metri
                    </p>
                </div>
            `);
            layerGroups.tper.addLayer(marker);
        });
    } catch (e) {
        console.error("Errore fetch fermate TPER:", e);
    }
}

/**
 * Caricamento Layer Vettoriali Globali (Piste ciclabili e Parchi)
 */
async function loadGlobalLayers() {
    // 1. Piste Ciclabili GeoJSON
    try {
        const res = await fetch(`${API_BASE}/api/mobility/bikepaths?limit=1500`);
        if (res.ok) {
            const geojson = await res.json();
            L.geoJSON(geojson, {
                style: {
                    color: "#06b6d4",
                    weight: 3.5,
                    opacity: 0.8
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`
                        <div class="popup-content">
                            <span class="popup-tag" style="background: rgba(6,182,212,0.15); color: #06b6d4;">PISTA CICLABILE</span>
                            <h4>${feature.properties.tipologia || "Corsia ciclabile"}</h4>
                        </div>
                    `);
                }
            }).addTo(layerGroups.ciclabili);
        }
    } catch (e) {
        console.warn("Impossibile caricare piste ciclabili:", e);
    }

    // 2. Aree Verdi GeoJSON
    try {
        const res = await fetch(`${API_BASE}/api/green/areas?limit=500`);
        if (res.ok) {
            const geojson = await res.json();
            L.geoJSON(geojson, {
                style: {
                    color: "#10b981",
                    weight: 1.5,
                    fillColor: "#10b981",
                    fillOpacity: 0.25
                },
                pointToLayer: (feature, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 5,
                        color: "#10b981",
                        fillColor: "#10b981",
                        fillOpacity: 0.6
                    });
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`
                        <div class="popup-content">
                            <span class="popup-tag parco">AREA VERDE</span>
                            <h4>${feature.properties.nome || "Parco cittadino"}</h4>
                        </div>
                    `);
                }
            }).addTo(layerGroups.verdi);
        }
    } catch (e) {
        console.warn("Impossibile caricare aree verdi:", e);
    }
}

/**
 * 4. Diagnostica Salute API
 */
async function checkApiHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();
        if (data.status === "healthy") {
            dom.apiStatusBadge.className = "status-badge connected";
            dom.apiStatusText.textContent = "API & PostGIS 3.3 Online";
        } else {
            dom.apiStatusBadge.className = "status-badge error";
            dom.apiStatusText.textContent = "DB Non Connesso";
        }
    } catch (e) {
        dom.apiStatusBadge.className = "status-badge error";
        dom.apiStatusText.textContent = "API Offline";
    }
}

/**
 * 5. Event Listeners e Interfaccia Utente
 */
function setupEventListeners() {
    // Toggle Sidebar
    dom.btnToggleSidebar.addEventListener("click", () => {
        dom.sidebar.classList.toggle("collapsed");
        setTimeout(() => map.invalidateSize(), 300);
    });

    // Slider Raggio
    dom.radiusSlider.addEventListener("input", (e) => {
        state.radius = parseInt(e.target.value);
        dom.radiusValueBadge.textContent = `${state.radius} m`;
        if (bufferCircle) {
            bufferCircle.setRadius(state.radius);
        }
    });

    dom.radiusSlider.addEventListener("change", () => {
        refreshData();
    });

    // Preset Chips
    dom.chips.forEach(chip => {
        chip.addEventListener("click", () => {
            dom.chips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");

            const lat = parseFloat(chip.dataset.lat);
            const lon = parseFloat(chip.dataset.lon);
            map.flyTo([lat, lon], 15, { duration: 1 });
            setNewLocation(lat, lon);
        });
    });

    // Toggle Layers
    setupLayerToggle(dom.toggleUnibo, "unibo");
    setupLayerToggle(dom.toggleBiblio, "biblioteche");
    setupLayerToggle(dom.toggleTper, "tper");
    setupLayerToggle(dom.toggleCiclabili, "ciclabili");
    setupLayerToggle(dom.toggleVerdi, "verdi");
    setupLayerToggle(dom.toggleRacks, "rastrelliere");

    // Slider Preferenze
    setupWeightSlider(dom.weightStudy, dom.weightStudyVal, "study");
    setupWeightSlider(dom.weightTransit, dom.weightTransitVal, "transit");
    setupWeightSlider(dom.weightBike, dom.weightBikeVal, "bike");
    setupWeightSlider(dom.weightGreen, dom.weightGreenVal, "green");

    // Time Chips (Temporal Scenario)
    dom.timeChips.forEach(chip => {
        chip.addEventListener("click", () => {
            dom.timeChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            const hourVal = chip.dataset.hour;
            state.hour = hourVal === "now" ? "now" : parseInt(hourVal);
            fetchAccessibilityEvaluation();
        });
    });
}

function setupLayerToggle(checkbox, layerKey) {
    checkbox.addEventListener("change", (e) => {
        const isChecked = e.target.checked;
        state.layers[layerKey] = isChecked;
        if (isChecked) {
            layerGroups[layerKey].addTo(map);
        } else {
            layerGroups[layerKey].removeFrom(map);
        }
    });
}

function setupWeightSlider(slider, badge, key) {
    slider.addEventListener("input", (e) => {
        state.weights[key] = parseInt(e.target.value);
        badge.textContent = `${state.weights[key]}%`;
    });
    slider.addEventListener("change", () => {
        fetchAccessibilityEvaluation();
    });
}

// Avvio Applicazione
document.addEventListener("DOMContentLoaded", () => {
    checkApiHealth();
    initMap();
    setupEventListeners();
    refreshData();
    loadGlobalLayers();
});
