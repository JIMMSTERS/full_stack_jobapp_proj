# OfferFlow Backend

Python + FastAPI service backing OfferFlow, with PostgreSQL as the primary datastore.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running locally or in a container)

## Setup

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000 and interactive docs at
http://127.0.0.1:8000/docs.

## Structure

```
backend/
├── app/
│   ├── __init__.py
│   └── main.py        # FastAPI app entry point
├── requirements.txt
└── README.md
```
