// QuakeScope — a static, multi-view website.
// Handles switching between Home / Map / Findings / About, and builds the map.

// ---------------- view switching ----------------
const VIEW_IDS = { home: "home", map: "map-view", findings: "findings", about: "about" };

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById(VIEW_IDS[name] || "home").classList.add("active");
  document.querySelectorAll("#nav .links a").forEach((a) =>
    a.classList.toggle("active", a.dataset.view === name));
  window.scrollTo(0, 0);
  if (name === "map") openMap();
}
document.querySelectorAll("[data-view]").forEach((el) =>
  el.addEventListener("click", () => showView(el.dataset.view)));

// ---------------- the map (built once, the first time it is opened) ----------------
let map, quakeLayer, zoneLayer, ALL_QUAKES = [], mapReady = false;
const WORLD = [[-85, -180], [85, 180]];

function depthColour(km) {
  if (km < 70) return "#d7263d";    // shallow      — red
  if (km < 300) return "#f4a000";   // intermediate — amber
  return "#5b2a86";                 // deep         — purple
}
function magRadius(m) { return Math.max(2.5, (m - 4) ** 1.7); }

function buildMap() {
  map = L.map("map", {
    preferCanvas: true, minZoom: 2, maxZoom: 8,
    maxBounds: WORLD, maxBoundsViscosity: 1.0,   // stops the endless left/right scrolling
  }).setView([10, 140], 3);

  L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
    { attribution: "Tiles &copy; Esri &nbsp;|&nbsp; Earthquakes &copy; USGS",
      noWrap: true, bounds: WORLD, maxZoom: 8 }       // noWrap = one world, not infinite copies
  ).addTo(map);

  quakeLayer = L.layerGroup().addTo(map);
  zoneLayer = L.layerGroup().addTo(map);
  L.control.layers(null, { "Earthquakes": quakeLayer, "Risk zones": zoneLayer }).addTo(map);
  addLegend();
}

function popupHtml(q) {
  return `<b>M${q.mag}</b> &nbsp; ${q.place}<br>depth ${q.depth} km` +
    (q.tsunami ? " &nbsp;🌊 tsunami" : "") +
    `<br><span style="color:#666">${q.time.replace("T", " ").replace("Z", " UTC")}</span>`;
}

function drawQuakes(minMag) {
  quakeLayer.clearLayers();
  let shown = 0;
  for (const q of ALL_QUAKES) {
    if (q.mag < minMag) continue;
    L.circleMarker([q.lat, q.lon], {
      radius: magRadius(q.mag), color: "#ffffff", weight: 0.5,
      fillColor: depthColour(q.depth), fillOpacity: 0.85,
    }).bindPopup(() => popupHtml(q)).addTo(quakeLayer);   // popup text is built lazily, on click
    shown++;
  }
  document.getElementById("count").textContent = shown.toLocaleString() + " shown";
}

function drawZones(zones) {
  for (const z of zones) {
    L.circleMarker([z.lat, z.lon], {
      radius: z.risk_score / 4, color: "#7a2e1e", weight: 2,
      fillColor: "#c0612e", fillOpacity: 0.2,
    })
      .bindPopup(`<b>${z.top_region}</b><br>risk score <b>${z.risk_score}</b> / 100<br>` +
                 `${z.n_events.toLocaleString()} quakes &middot; strongest M${z.max_magnitude}`)
      .on("click", (e) => map.flyTo(e.latlng, 5))     // click a zone to fly to it
      .addTo(zoneLayer);
  }
}

function addLegend() {
  const legend = L.control({ position: "bottomright" });
  legend.onAdd = () => {
    const d = L.DomUtil.create("div", "legend");
    d.innerHTML =
      "<b>Depth of quake</b>" +
      '<span class="dot" style="background:#d7263d"></span>shallow (under 70 km)<br>' +
      '<span class="dot" style="background:#f4a000"></span>intermediate (70 to 300 km)<br>' +
      '<span class="dot" style="background:#5b2a86"></span>deep (over 300 km)<br>' +
      '<span class="dot" style="background:#c0612e"></span>risk zone (size = risk)<br>' +
      '<span style="color:#777">dot size = magnitude</span>';
    return d;
  };
  legend.addTo(map);
}

async function openMap() {
  if (!map) buildMap();
  map.invalidateSize();               // the container was hidden; recompute its real size
  if (mapReady) return;
  const loading = document.getElementById("loading");
  loading.style.display = "flex";
  try {
    const [quakes, zones] = await Promise.all([
      fetch("data/quakes.json").then((r) => r.json()),
      fetch("data/zones.json").then((r) => r.json()),
    ]);
    ALL_QUAKES = quakes;
    drawQuakes(6);
    drawZones(zones);
    mapReady = true;
  } catch (err) {
    loading.textContent = "could not load the earthquake data";
    return;
  }
  loading.style.display = "none";
}

document.querySelectorAll("#bar button").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!mapReady) return;
    document.querySelectorAll("#bar button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    drawQuakes(Number(btn.dataset.mag));
  });
});
