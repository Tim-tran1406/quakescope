// QuakeScope map — plain JavaScript that calls our FastAPI and draws the data.
// Served by FastAPI at /app, so the API is at the same address ("" = same origin).
const API = "";

// 1) Make the map and add a background of map tiles.
const map = L.map("map", { worldCopyJump: true }).setView([10, 150], 3);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap", maxZoom: 10,
}).addTo(map);

// Two layers we can toggle on/off: the quakes, and the risk zones.
const quakeLayer = L.layerGroup().addTo(map);
const zoneLayer = L.layerGroup().addTo(map);
L.control.layers(null, { "Earthquakes": quakeLayer, "Risk zones": zoneLayer }).addTo(map);

// --- helpers --------------------------------------------------------------
// Colour a quake by how deep it is (shallow quakes are the most damaging).
function depthColour(km) {
  if (km < 70) return "#d93025";        // shallow  – red
  if (km < 300) return "#f9ab00";       // mid      – amber
  return "#1a73e8";                     // deep     – blue
}
// Bigger magnitude → bigger dot (squared so big quakes really stand out).
function magRadius(m) { return Math.max(3, (m - 4) ** 2); }

// --- the earthquakes ------------------------------------------------------
async function loadQuakes(minMag) {
  const res = await fetch(`${API}/quakes?min_magnitude=${minMag}&limit=5000`);
  const quakes = await res.json();
  quakeLayer.clearLayers();
  for (const q of quakes) {
    L.circleMarker([q.latitude, q.longitude], {
      radius: magRadius(q.magnitude),
      color: depthColour(q.depth_km), weight: 1,
      fillColor: depthColour(q.depth_km), fillOpacity: 0.55,
    }).bindPopup(
      `<b>M${q.magnitude}</b> — ${q.place}<br>` +
      `depth ${q.depth_km} km<br>` +
      `${new Date(q.event_time).toUTCString()}` +
      (q.tsunami ? "<br>🌊 tsunami flag" : "")
    ).addTo(quakeLayer);
  }
  document.getElementById("count").textContent = `${quakes.length.toLocaleString()} quakes`;
}

// --- the risk zones -------------------------------------------------------
async function loadZones() {
  const res = await fetch(`${API}/zones/risk?limit=30`);
  const zones = await res.json();
  for (const z of zones) {
    L.circleMarker([z.centroid_lat, z.centroid_lon], {
      radius: z.risk_score / 4,
      color: "#a50e0e", weight: 2, fillColor: "#e8743b",
      fillOpacity: 0.25,
    }).bindPopup(
      `<b>${z.top_region}</b><br>` +
      `risk score: <b>${z.risk_score}</b> / 100<br>` +
      `${z.n_events.toLocaleString()} quakes, strongest M${z.max_magnitude}`
    ).addTo(zoneLayer);
  }
}

// --- legend ---------------------------------------------------------------
const legend = L.control({ position: "bottomright" });
legend.onAdd = () => {
  const div = L.DomUtil.create("div", "legend");
  div.innerHTML =
    "<b>Depth of quake</b>" +
    '<span class="dot" style="background:#d93025"></span>shallow (&lt;70 km)<br>' +
    '<span class="dot" style="background:#f9ab00"></span>medium (70–300 km)<br>' +
    '<span class="dot" style="background:#1a73e8"></span>deep (&gt;300 km)<br>' +
    '<span class="dot" style="background:#e8743b"></span>risk zone (size = risk)';
  return div;
};
legend.addTo(map);

// --- wire up the magnitude buttons ---------------------------------------
document.querySelectorAll("#bar button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#bar button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    loadQuakes(btn.dataset.mag);
  });
});

// --- first load -----------------------------------------------------------
loadQuakes(6);
loadZones();
