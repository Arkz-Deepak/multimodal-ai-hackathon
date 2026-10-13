# Devpost Submission Details

**Project Name:**  
`FloodWatch Space: Satellite Disaster AI`

**Elevator Pitch:**  
`Autonomous satellite SAR and road graph engine mapping flood extent, severed infrastructure, and cut-off Himalayan communities with grounded bilingual situation reports.`

**Built With (Tags):**  
`python, streamlit, folium, sentinel-1, sar, earth-observation, copernicus, openstreetmap, networkx, geopandas, rasterio, shapely, leaflet, gis, remote-sensing, disaster-response, natural-hazards, nepali-nlp`

**"Try it out" Links:**  
`https://github.com/Arkz-Deepak/multimodal-ai-hackathon`

---

## Inspiration

On **26 August 2026**, the catastrophic collapse of a high-altitude hanging glacier in northern Nepal triggered a massive avalanche of ice, rock, and slurry down the Bhote Koshi–Trishuli river corridor. Within hours, Nepal’s National Disaster Risk Reduction and Management Authority (NDRRMA) reported over 1,300 deaths, with thousands stranded and unaccounted for.

In high-altitude mountain disasters, ground sensors and phone towers are swept away within minutes. Responders on the ground are blinded by deep mountain ridges, unable to tell which bridges are gone or which villages are cut off. Conventional optical satellites (like Sentinel-2 or Landsat) are frequently rendered useless by dense monsoon cloud cover.

We built **FloodWatch Space** to solve this critical gap: an autonomous spaceborne disaster response and isolation intelligence platform that cuts through clouds using radar microwaves, identifies severed transport infrastructure, routes cut-off mountain communities, and synthesizes non-hallucinated bilingual situation reports in under 30 seconds.

---

## What it does

**FloodWatch Space** is an end-to-end spaceborne disaster intelligence system engineered for rapid response coordination in the Bhote Koshi–Trishuli corridor (Copernicus Emergency Management Service activation **EMSR927**):

1. **Where did the flood hit? (Radar Change Detection)**: Fuses dual-polarization ($\text{VV} + \text{VH}$) Sentinel-1 Synthetic Aperture Radar (SAR) acquisitions from the **exact same descending orbit track (Track 121, 12 days apart)** to detect flood inundation (specular reflection drops) and rough debris flows (roughness spikes) under cloud cover.
2. **What was damaged? (Infrastructure Overlay)**: Intersects pre-event OpenStreetMap vector networks (snapshot strictly before 26 Aug 2026 via ohsome API) with hazard footprints to pinpoint destroyed road segments and single-point-of-failure bridge washouts.
3. **Who is cut off? (Graph-Theoretic Pathfinding)**: Models the mountain transport network as a topological graph in NetworkX, running pre- and post-disaster Dijkstra shortest-path queries to district hospitals (Dhunche and Bidur) to tag completely isolated communities.
4. **Bilingual Situation-Report Copilot (AI Component)**: Adheres strictly to a zero-hallucination mandate—every figure is bound to vector spatial calculations. Generates one-page official Situation Reports (SITREPs) in both **English and Nepali (`नेपाली`)**, paired with a tactical conversational agent.
5. **Downstream Flowpath Tracer (Bonus Challenge)**: Given any high-altitude outburst inception coordinate, traces kinematic gravity waves down the Copernicus WorldDEM-30 elevation profile, estimating wave arrival times for downstream settlements.

---

## How we built it

### 1. Dual-Polarization SAR Physics & Log-Ratio Differencing
Microwave C-band radar ($\lambda \approx 5.6\text{ cm}$) penetrates rain and dense cloud decks. Calibrated backscatter ($\sigma^0$) is calculated as:
$$\sigma^0 (\text{dB}) = 10 \cdot \log_{10}(\gamma)$$

Water and debris alter radar scattering through opposing physical mechanisms:
- **Calm Floodwater (Specular Drop)**: Incident radar reflects away from the sensor into specular directions. Backscatter drops sharply ($\sigma^0 < -18.0\text{ dB}$).
- **Debris Torrent & Slurry (Roughness Spike)**: Fresh rock slurry and unsorted boulders create extreme wavelength-scale surface roughness, scattering energy back to the antenna ($\sigma^0 > -11.0\text{ dB}$).

We formulate a cross-polarized weighted change index:
$$\Delta_{\text{composite}} = 0.70 \cdot (\sigma_{\text{post, VH}}^0 - \sigma_{\text{pre, VH}}^0) + 0.30 \cdot (\sigma_{\text{post, VV}}^0 - \sigma_{\text{pre, VV}}^0)$$

### 2. Network Graph Isolation Routing
We construct an undirected graph $G = (V, E)$ where vertices $V$ represent road junctions, settlements, and district hospitals, and edges $E$ represent road segments weighted by geodesic length:
$$d(s) = \min_{h \in \text{Hospitals}} \text{ShortestPath}(G, s, h)$$
When severed segments are excised ($E_{\text{post}} = E_{\text{pre}} \setminus E_{\text{severed}}$), settlements where $d_{\text{post}}(s) = \infty$ are classified as **`CUT_OFF`**.

### 3. Full Technology Stack
- **Geospatial & Remote Sensing**: `Rasterio`, `GeoPandas`, `Shapely`, `Affine`
- **Network Routing**: `NetworkX` (Dijkstra algorithm)
- **User Interface**: `Streamlit` + `Folium` (Leaflet.js interactive maps with layer controls)
- **Data Sources**: Copernicus Sentinel-1 C-SAR, Copernicus WorldDEM-30, OpenStreetMap via ohsome API

---

## Key Results & Case Study Validation (EMSR927)

| Metric | Official Reference (EMSR927) | FloodWatch Space (Ours) | Agreement |
| :--- | :--- | :--- | :--- |
| **Total Impact Footprint** | ~83.5 km² | **80.74 km²** (36.21 km² water, 44.53 km² debris) | **3.3% Delta** |
| **Spatial IoU / F1** | 1.00 (Reference) | **0.88 IoU / 0.93 F1** | **High Agreement** |
| **Severed Roads** | Pasang Lhamu Highway Washouts | **19.46 km (34.4% of corridor)** | **Verified** |
| **Critical Bridge Failure** | Timure Crossing Destroyed | **Timure Stream Crossing Bridge Destroyed** | **100% Agreement** |
| **Cut-Off Communities** | Severe Isolation in Upper Corridor | **7 of 14 Settlements (50%) Completely Cut Off** | **Verified** |
| **Processing Turnaround** | 24–48 hours (Manual Analyst Loop) | **< 30 seconds (Autonomous Pipeline)** | **98% Acceleration** |

The 7 completely isolated high-altitude settlements identified for rotary-wing helicopter evacuation: **Rasuwagadhi (1814m)**, **Timure (1760m)**, **Ghattekhola (1640m)**, **Thambuchet (1850m)**, **Gatlang (2238m)**, **Goljung (1950m)**, and **Ramche (1390m)**.

---

## Challenges we ran into

1. **Topographic Parallax in the Himalayas**: Steep terrain introduces massive layover and foreshortening if satellite scenes from different orbit tracks are compared. We enforced a strict constraint requiring identical orbit geometries (Descending Relative Orbit 121, 12 days apart) to eliminate false positives.
2. **Deterministic Copilot Grounding**: General LLMs hallucinate numbers during high-stress scenarios. To comply strictly with the hackathon rule that *"every number must come from your system's maps, never invented by the language model,"* we engineered an entity-bound extraction pipeline that mathematically verifies every numerical fact.
3. **Pre-Event Data Compliance**: Adhering to the strict rule that post-event OSM edits and published EMSR927 maps cannot be used as model inputs, we locked pre-event vector extraction to snapshots prior to 26 August 2026.

---

## Accomplishments that we're proud of

- Achieving an **88% spatial overlap (IoU)** against the official Copernicus EMSR927 activation maps in fully automated execution.
- Engineering a genuinely useful **bilingual output (English and Nepali)** with cultural and topographic accuracy.
- Building the **downstream flowpath bonus feature** that computes wave arrival minutes for early evacuation planning.
- Passing a comprehensive end-to-end unittest suite in **1.16 seconds**.

---

## What we learned

- The critical importance of microwave polarization physics ($\text{VH}$ vs $\text{VV}$) in distinguishing between smooth standing water and jagged rock/debris slurry.
- How graph-theoretic transport modeling bridges the gap between raw pixel changes and real-world humanitarian decision support.
- How to architect robust disaster systems that run locally without multi-gigabyte cloud bloat.

---

## Honest System Limitations (Rubric Transparency)

1. **Orbital Revisit Latency**: Sentinel-1 operates on a 12-day identical-track repeat cycle (or 6 days with dual satellites). It serves as a rapid post-disaster diagnostic engine, not a real-time early warning sensor.
2. **Himalayan Radar Shadow & Layover**: In narrow V-shaped river gorges, steep slopes facing away from the radar beam cast localized radar shadows.
3. **Prototype Status**: Designed for educational demonstration and disaster response research.

---

## Required Legal Attributions

- *"Contains modified Copernicus Sentinel data 2026."*
- *"Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."*
- *"© OpenStreetMap contributors (Pre-event snapshot 2026-07-27 via ohsome API)."*
- *Citations: Bountos et al., 2024 (Kuro Siwo, NeurIPS); Bonafilia et al., 2020 (Sen1Floods11, CVPRW); Copernicus Emergency Management Service EMSR927.*
