# Session 07 — Polish & reproducibility (Phase 7)

**What we did:** turned a working project into a *presentable, reproducible* one — the
part that makes a portfolio project look professional rather than like a pile of scripts.

![What run_all.sh rebuilds](images/architecture.png)

---

## Why this phase matters

A recruiter or teammate spends about 30 seconds deciding if your project is any good.
They look at two things: **the README**, and **whether they can run it**. Phase 7 nails
both.

### 1. The README — your project's front door
`README.md` is the first (often only) thing people read. Ours leads with a screenshot,
states what the project does, lists the **findings** (the actual insights — the part
that stands out), shows the stack and architecture, and gives copy-paste run steps.

*Tip you can reuse:* lead with results, not setup. "Earthquakes aren't increasing
(p = 0.93)" is far more compelling than "this project uses Python and PostgreSQL."

### 2. Reproducibility — pinned dependencies
```
pandas==3.0.3
scikit-learn==1.9.0
```
We pinned **exact versions** in `requirements.txt`. Without the `==`, someone installing
next year could get newer libraries that behave differently and break things. Pinning
means *anyone* can recreate the exact environment that produced these results.

We split tools that only build the docs/screenshots into `requirements-dev.txt`, so the
core project stays lean.

### 3. One command to rebuild everything
```bash
./run_all.sh
```
This script runs the whole pipeline in order — ingest → load → SQL → all six analyses —
so the entire project can be regenerated from nothing. Two habits made this possible,
which we built in earlier:
- **idempotent steps** (ingest *resumes*, load_raw drops & recreates) → safe to re-run.
- **clear separation** — one script per job — so the order is obvious.

### 4. A clean repository (`.gitignore`)
The repo deliberately **excludes** three things:
- `data/raw/` — 93 MB of re-downloadable data (code, not data, belongs in git).
- `.venv/` — the installed libraries (rebuilt from `requirements.txt`).
- `.env` — database secrets (never commit credentials).

So what's on GitHub is exactly what matters: the code, the SQL, the docs, the README.

---

## The project, end to end
One database in the middle; everything else either fills it or reads from it:

> USGS → `ingest.py` → `load_raw.py` → **PostgreSQL** → SQL `staging` → 6 analyses → `analytics`
> → **FastAPI** → web map / Power BI

## Optional next step — free cloud deploy
To put it online for free you'd typically: host PostgreSQL on a free tier (e.g.
Supabase), deploy the FastAPI app on a free host (e.g. Render or Railway), and point the
map at that URL. Left as an optional follow-up — it needs accounts and secrets, which
are yours to create.

## What's left
- **Phase 6 — Power BI** (deferred): connect Power BI to this same PostgreSQL database
  and build a BI dashboard, once a Windows environment is set up.

The project is now complete and presentable as a full-stack data project: **ingestion →
database → data science → API → interactive map**, reproducible with one command.
