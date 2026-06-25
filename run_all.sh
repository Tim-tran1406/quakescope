#!/usr/bin/env bash
# Rebuild the entire QuakeScope pipeline from scratch, in order.
# Usage:  ./run_all.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
PSQL="$(command -v psql || echo /opt/homebrew/opt/postgresql@17/bin/psql)"

echo "==> 1/4  Ingest earthquakes from the USGS"
$PY src/ingest.py

echo "==> 2/4  Load the raw JSON into PostgreSQL"
$PY src/load_raw.py

echo "==> 3/4  Build the clean staging table (SQL)"
"$PSQL" -d quakescope -f sql/staging_events.sql

echo "==> 4/4  Run the data science (writes to the analytics schema)"
for step in cluster bvalue trend omori anomalies risk; do
  echo "    - $step"
  $PY "src/$step.py"
done

echo
echo "Done. Start the app with:"
echo "    .venv/bin/uvicorn api.main:app --reload"
echo "Then open  http://127.0.0.1:8000/app/  (map)  and  /docs  (API)."
