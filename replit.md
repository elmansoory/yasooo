# Skating Analysis & Attendance System (yasooo)

## Overview
A Streamlit-based web application for figure skating clubs to manage member data, track attendance, handle payments, and analyze athlete performance.

## Tech Stack
- **Framework:** Streamlit (Python)
- **Database:** SQLite (`skating_database.db`)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Plotly
- **Language:** Python 3.12

## Project Structure
- `app.py` — Main entry point (dashboard, member profiles, reports)
- `setup_database.py` — Database initialization with sample data
- `src/` — Core source code (AI, database models, pages, utils)
- `data/` — Exported reports and processed data
- `docs/` — Documentation (English & Arabic)

## Running the App
The app runs via the "Start application" workflow:
```
python -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
```

## Database Setup
Run `python setup_database.py` to initialize the SQLite database with sample data.

## Features
- Member management with profiles, levels, and coaches
- Attendance tracking with monthly/daily reports
- Payment/membership management
- Interactive charts (attendance trends, level distribution, top members)
- Arabic language UI
- Excel import ("📥 استيراد بيانات" page): upload a monthly roster/payments/attendance
  workbook, get a full preview (new members, field updates, new/duplicate payments,
  new/duplicate attendance, unmatched attendance names) before anything is saved, then
  confirm to commit. Safe to re-upload the same file — duplicates are always skipped.
  Logic lives in `src/importer/parser.py` (pure parsing/classification) and
  `src/importer/service.py` (DB diff + commit).

## Dependencies
See `requirements-minimal.txt` for core dependencies (Streamlit, Pandas, Plotly, SQLAlchemy).
Full AI/ML dependencies are in `requirements.txt` (not installed by default).
