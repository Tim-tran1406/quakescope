// QuakeScope map — a plain STATIC website.
// It loads two pre-exported JSON files (no backend, no database, nothing secret)
// and draws them with Leaflet. Everything runs in the visitor's browser.

// preferCanvas keeps ~30,000 dots smooth. maxZoom matches the basemap's tiles.
const map = L.map("map", { worldCopyJump: true, preferCanvas: true, minZoom: 2, maxZoom: 8 })
  .setView([5, 150], 3);

// Earthy physical-geography basemap (terrain + ocean depth), no API key needed.
L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
  { attribution: "Tiles &copy; Esri &nbsp;|&nbsp; Earthquakes &copy; USGS", maxZoom: 8 }
).addTo(map);

const quakeLayer = L.layerGroup().addTo(map);
const zoneLayer = L.layerGroup().addTo(map);
L.control.layers(null, { "Earthquakes": quakeLayer, "Risk zones": zoneLayer }).addTo(map);

// Colour by depth (chosen to stand out on the earthy basemap).
function depthColour(km) {
  if (km < 70) return "#d7263d";    // shallow      — red
  if (km < 300) return "#f4a000";   // intermediate — amber
  return "#5b2a86";                 // deep         — purple
}
function magRadius(m) { return Math.max(2.5, (m - 4) ** 1.7); }

let ALL_QUAKES = [];

function drawQuakes(minMag) {
  quakeLayer.clearLayers();
  let shown = 0;
  for (const q of ALL_QUAKES) {
    if (q.mag < minMag) continue;
    L.circleMarker([q.lat, q.lon], {
      radius: magRadius(q.mag),
      color: "#ffffff", weight: 0.5,
      fillColor: depthColour(q.depth), fillOpacity: 0.85,
    }).bindPopup(
      `<b>M${q.mag}</b> &nbsp; ${q.place}<br>` +
      `depth ${q.depth} km` + (q.tsunami ? " &nbsp;🌊 tsunami" : "") +
      `<br><span style="color:#666">${q.time.replace("T", " ").replace("Z", " UTC")}</span>`
    ).addTo(quakeLayer);
    shown++;
  }
  document.getElementById("count").textContent = shown.toLocaleString() + " shown";
}

function drawZones(zones) {
  for (const z of zones) {
    L.circleMarker([z.lat, z.lon], {
      radius: z.risk_score / 4,
      color: "#7a2e1e", weight: 2, fillColor: "#c0612e", fillOpacity: 0.2,
    }).bindPopup(
      `<b>${z.top_region}</b><br>risk score <b>${z.risk_score}</b> / 100<br>` +
      `${z.n_events.toLocaleString()} quakes &middot; strongest M${z.max_magnitude}`
    ).addTo(zoneLayer);
  }
}

async function init() {
  const [quakes, zones] = await Promise.all([
    fetch("data/quakes.json").then((r) => r.json()),
    fetch("data/zones.json").then((r) => r.json()),
  ]);
  ALL_QUAKES = quakes;
  drawQuakes(6);
  drawZones(zones);
}

document.querySelectorAll("#bar button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#bar button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    drawQuakes(Number(btn.dataset.mag));
  });
});

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

init();
