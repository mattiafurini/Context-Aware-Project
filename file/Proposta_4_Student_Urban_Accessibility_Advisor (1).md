# Analisi e Strategia d'Esame

## Perché la Proposta 4 è la scelta migliore

* **Nessun obbligo di sviluppare un'App Mobile:** A differenza delle proposte 1 e 2, la Proposta 4 specifica che l'app mobile è opzionale. È possibile completare il progetto sviluppando unicamente una dashboard Web, dimezzando il lavoro sul frontend.
* **Complessità delegata a PostGIS:** Le funzionalità spaziali richieste (buffer, densità, punti vicini) sono nativamente gestite dal database spaziale PostgreSQL/PostGIS tramite query SQL (es. `ST_Buffer`, `ST_DWithin`). Questo evita di dover implementare algoritmi complessi lato codice.
* **Dati reali e pronti all'uso:** Sfrutta i dataset aperti del Comune di Bologna, i dati GTFS di TPER e OpenStreetMap, facilmente reperibili ed esportabili senza dover creare simulatori articulati.

---

## Strategia per raggiungere 30 e Lode (Proposta 4)

Per coprire sia la base che i punti bonus con il minimo sforzo realizzativo:

* **Progetto Base (18 pt):** Database PostGIS con 4 layer Open Data (es. fermate TPER, biblioteche, sale studio, piste ciclabili), backend REST per interrogare i PoI e dashboard Leaflet/OpenLayers con mappa interattiva.
* **Containerizzazione (+2 pt):** Setup con `docker-compose.yml` contenente i 3 container: database, backend (Python/Node) e frontend.
* **Profilazione utente e ranking (+2 pt):** Calcolo di uno score pesato in base a form con slider delle preferenze dell'utente (es. peso trasporti = 80%, peso aree verdi = 20%).
* **Analisi spaziale dei servizi (+2 pt):** Generazione di zone di rispetto (buffer) o heatmap tramite funzioni PostGIS o librerie Leaflet pronte all'uso.
* **Recommendation engine (+2 pt):** Generazione di un testo esplicativo accanto allo score (es. *"Area altamente consigliata per presenza di piste ciclabili e biblioteche"*).
* **Temporal analytics (+2 pt):** Un semplice filtro temporale/orario per mostrare solo i servizi aperti in una determinata fascia oraria.
* **Privacy location-aware (+2 pt):** Aggiunta di una funzione nel backend che applica un leggero rumore casuale (perturbazione) alle coordinate dell'utente prima di effettuare la ricerca.

---

# Proposta 4 – Student Urban Accessibility Advisor

**Focus:** spatial recommendation systems, urban analytics, open data integration, context-aware services

---

### Descrizione generale

Si chiede di realizzare una piattaforma context-aware per supportare studenti universitari nell'analisi dell'accessibilità urbana e della qualità dei servizi disponibili nelle diverse aree della città. Il sistema deve integrare dati spaziali provenienti da fonti open data eterogenee, ad esempio:

* Trasporto pubblico
* Sedi universitarie
* Biblioteche
* Mense
* Piste ciclabili
* Aree verdi
* Sale studio
* Servizi commerciali
* Mobilità sostenibile

L'obiettivo della piattaforma è generare indicatori spaziali e suggerimenti relativi alle aree della città più adatte alla vita universitaria, sulla base delle preferenze dell'utente e del contesto corrente. Ad esempio:

* Uno studente potrebbe preferire aree ben collegate tramite autobus;
* Un altro potrebbe preferire zone ricche di biblioteche e sale studio;
* Un altro ancora potrebbe privilegiare mobilità sostenibile e presenza di piste ciclabili.

Il sistema non deve limitarsi a visualizzare una mappa statica. La componente context-aware deve essere esplicita: il sistema deve utilizzare almeno due informazioni contestuali, ad esempio posizione, orario, densità dei servizi o preferenze utente, per generare suggerimenti differenti a seconda dello scenario.

Il progetto deve inoltre integrare:

* Funzionalità GIS;
* Query spaziali;
* Ranking geografici;
* Dashboard interattive;
* Analisi spaziali dei servizi urbani.

---

### 4.1 Componenti

#### **Base 18 pt – Applicazione base**
* Integrazione di almeno 4 dataset open data differenti relativi alla città di Bologna.
* Database spaziale per la gestione dei layer geografici tramite PostGIS.
* Dashboard Web con mappa interattiva multilayer.
* Visualizzazione su mappa dei dati spaziali:
  * Sedi universitarie
  * Fermate TPER
  * Biblioteche
  * Mense
  * Piste ciclabili
  * Sale studio
  * Aree verdi
* Sistema base di ranking delle aree urbane basato su almeno due fattori contestuali, e.g. distanza dai servizi e accessibilità tramite trasporto pubblico.
* API REST per interrogazione dei servizi vicini a una posizione.
* Possibilità di selezionare un'area della città e visualizzarne indicatori aggregati.
* Dashboard Web per visualizzazione dei layer geografici e dei suggerimenti contestuali.

#### **+2 pt – Profilazione utente e ranking personalizzato**
* Definizione di preferenze configurabili da parte dello studente, e.g.:
  * Importanza del trasporto pubblico
  * Preferenza per mobilità sostenibile
  * Interesse per biblioteche o sale studio
  * Preferenza per aree verdi
* Ranking dinamico delle aree urbane sulla base delle preferenze configurate.
* Possibilità di confrontare ranking differenti per utenti diversi.
* Storico dei suggerimenti generati dal sistema.

#### **+2 pt – Analisi spaziale dei servizi urbani**
* Implementazione di buffer analysis e density analysis sui servizi urbani.
* Calcolo della densità dei punti di interesse nelle diverse aree della città.
* Heatmap relative alla distribuzione dei servizi universitari.
* Analisi delle aree maggiormente servite o maggiormente accessibili.

#### **+2 pt – Mobility analytics e trasporto pubblico**
* Integrazione di dati GTFS relativi al trasporto pubblico locale (TPER).
* Calcolo del tempo stimato di percorrenza verso le sedi universitarie.
* Analisi multimodale:
  * Walking
  * Biking
  * Trasporto pubblico
* Visualizzazione di isocrone temporali sulla mappa.
* Suggerimento delle aree più facilmente raggiungibili tramite trasporto pubblico.

#### **+2 pt – Recommendation engine context-aware**
* Generazione automatica di suggerimenti sulle aree più adatte alla vita universitaria.
* Calcolo di uno "Student Accessibility Score".
* Motivazione dei suggerimenti generati, e.g.:
  * "Area ben collegata"
  * "Alta densità di biblioteche"
  * "Presenza di piste ciclabili"
* Ranking dinamico delle zone urbane.

#### **+2 pt – Temporal analytics**
* Gestione di dati dipendenti dall'orario, esempio:
  * Orari biblioteche
  * Disponibilità servizi
  * Frequenza autobus
* Filtri temporali per fascia oraria o giorno della settimana.
* Analisi differenziata tra scenari diurni/notturni.

#### **+2 pt – Privacy location-aware**
* Integrazione di almeno una tecnica di privacy della posizione tra quelle viste a lezione.
* Possibilità di perturbare o anonimizzare la posizione utente.
* Valutazione delle metriche di:
  * Privacy Perturbation
  * Quality of Service
* Visualizzazione grafica del trade-off tra privacy e accuratezza dei suggerimenti.

#### **+2 pt – Analytics avanzata e clustering**
* Clustering delle aree urbane mediante algoritmi spaziali, e.g. K-Means o DBSCAN.
* Individuazione automatica delle zone maggiormente accessibili.
* Analisi di Moran per l'autocorrelazione spaziale di almeno 1 indicatore (es., densità delle biblioteche).
* Visualizzazione dei cluster su mappa.

#### **+2 pt – Containerizzazione con Docker Compose**
* Containerizzazione di:
  * Database
  * Back-end
  * Dashboard Web
* Script Docker Compose per l'avvio dell'intera piattaforma.
* Deployment opzionale mediante Kubernetes o minikube.

---

### 4.2 Tecnologie consigliate

* **App mobile opzionale:** Flutter, React Native, Android nativo o framework equivalente.
* **Back-end:** Python/FastAPI, Node.js o framework equivalente.
* **Database:** PostgreSQL + PostGIS.
* **Front-end:** OpenLayers o Leaflet.
* **Open data:**
  * OpenData Comune di Bologna
  * GTFS TPER
  * OpenStreetMap
  * Dataset derivati manualmente
* **Containerizzazione:** Docker, Kubernetes.

*È possibile utilizzare un qualsiasi linguaggio di programmazione o librerie a scelta dello studente.*
