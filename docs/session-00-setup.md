# Session 00 — Setup & the lay of the land

Welcome to **QuakeScope**. This doc explains what we're building, the tools
we'll use, and the one thing you need to install to get going. No prior
knowledge assumed — if a word is new, it's explained here.

---

## 1. What are we actually building?

A system that takes the world's earthquake records and turns them into
*insight*, presented two ways:

1. A **custom web app** — your own interactive map, powered by an API you write.
2. A **Power BI dashboard** — a business-intelligence report.

The thread running through all of it is **analysis**. We're not just going to
say "here are the earthquakes." We're going to answer real questions:

- Is seismic activity increasing, or do we just have better sensors now?
- Where is risk genuinely highest?
- Which quakes are part of a *swarm* vs. a one-off?
- How does the size-vs-frequency pattern differ region to region?

---

## 2. The tools, and *why* each one exists

Think of data flowing left-to-right through a pipeline. Each tool owns one job.

```
USGS API  →  Python  →  PostgreSQL  →  Python (data science)  →  FastAPI  →  Web map
                                    ↘                          ↘
                                     ──────────────────────────→  Power BI
```

- **Python** — a programming language that's the standard for working with data.
  We use it to *fetch* the earthquake data, *clean* it, and later *analyze* it.

- **PostgreSQL** (often just "Postgres") — a **database**. A database is a
  program whose whole job is to store large amounts of structured data and let
  you ask questions of it very fast. This is where your data *lives*.

- **SQL** — the **language you use to talk to a database**. "Show me every
  earthquake above magnitude 7 near Japan, by year" is one SQL query. This is
  the single most important skill for a data analyst, and you'll write a lot of it.

- **scikit-learn / SciPy** — Python libraries for **data science**: clustering,
  curve-fitting, statistics. This is the part that makes the project more than a
  pretty chart.

- **FastAPI** — a tool for building a **web API**. An API is a doorway that lets
  other programs (like your map website) request your data over the internet,
  e.g. "give me all quakes from last week as JSON."

- **Leaflet** — a free mapping library. We use it to draw the interactive
  earthquake map in the browser.

- **Power BI** — Microsoft's drag-and-drop tool for building dashboards. A core
  résumé skill for analyst roles.

---

## 3. What we set up today

I created the project folder at `~/quakescope` with this shape:

```
quakescope/
├── data/raw/        ← downloaded earthquake files land here (not committed to GitHub)
├── src/             ← our Python code
├── sql/             ← our SQL scripts
├── notebooks/       ← exploratory analysis (Phase 3)
├── docs/            ← these learning docs (you're reading session 00)
├── requirements.txt ← the list of Python tools we'll install
├── .env.example     ← a template for database settings
├── .gitignore       ← tells git which files to NOT upload
└── README.md
```

I also created a **virtual environment** (the hidden `.venv` folder).

> **What's a virtual environment?** A private, isolated box for *this project's*
> Python tools. Without it, every project shares one global pile of libraries and
> they eventually conflict ("project A needs version 1, project B needs version
> 2"). A venv keeps QuakeScope's tools separate and tidy. We'll "activate" it in
> Phase 1 before installing anything.

---

## 4. ✅ Installing PostgreSQL (done — here's exactly what we ran and why)

You already had **Homebrew** (a "package manager" — a tool that installs other
software with one command), so we used that instead of a manual download. Four
steps:

**Step 1 — install the database:**

```bash
brew install postgresql@17
```

This downloaded PostgreSQL 17 and automatically created the storage area where
your data will live.

**Step 2 — let your terminal find it.** Programs live in folders, and your
terminal only looks in certain folders (its `PATH`). We added PostgreSQL's folder
so the `psql` command works everywhere:

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc
```

**Step 3 — start the database server.** A database is a program that has to be
*running* to answer questions. This starts it in the background and re-starts it
whenever you log in:

```bash
brew services start postgresql@17
```

**Step 4 — create our project's database.** PostgreSQL can hold many separate
databases; we made one called `quakescope`:

```bash
createdb quakescope
```

**Check it worked:**

```bash
psql --version            # shows: psql (PostgreSQL) 17.10
psql -d quakescope -c "SELECT version();"   # connects and asks the DB about itself
```

Your login is `tim` with **no password** — normal and fine for local work. The
connection settings are saved in the project's `.env` file (kept on your Mac, not
uploaded) so our Python code can read them later.

*(Optional, for later: a visual database browser called **DBeaver Community** —
free at https://dbeaver.io — lets you click through tables instead of typing.
Purely optional; we can do everything from the terminal.)*

---

## 5. About Power BI (heads-up, not needed yet)

Power BI Desktop only runs on Windows, and you're on a Mac. We're handling this
by saving Power BI for the **last** phase, so it never blocks the fun parts.
When we get there, we'll set up a free Windows environment together. Until then,
everything runs natively on your Mac.

---

## 6. What's next

Once `psql --version` works, tell me and we start **Phase 1**: writing the
Python script that pulls real earthquake data from the USGS and saves it. You'll
see your first live data within minutes.
