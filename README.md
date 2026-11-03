# AutoCover

**A multi-provider vehicle insurance comparison platform** built with
React, TypeScript, FastAPI, and PostgreSQL.

AutoCover allows users to look up a vehicle by registration number,
compare normalized insurance quotes from multiple providers, review plan
details, and save a selected plan.

## Features

-   Vehicle lookup using the supplied vehicle registry.
-   Quote comparison across four providers with different data formats:
    -   Provider A: JSON
    -   Provider B: HTML and embedded JavaScript
    -   Provider C: PDF rate-card pricing calculation
    -   Provider D: CSV
-   Normalized quote data, including IDV, premiums, taxes, add-ons, and
    validity.
-   Separation of valid and expired quotes.
-   Provider declines and errors surfaced in the comparison response.
-   Cheapest valid quote identification.
-   Insurance plan selection and PostgreSQL persistence.
-   FastAPI Swagger documentation.

## Tech stack

  Layer             Technology
  ----------------- --------------------------------------------------
  Frontend          React, TypeScript, Vite
  Backend           Python, FastAPI, Pydantic
  Database          PostgreSQL
  ORM               SQLAlchemy
  Database driver   Psycopg 3
  PDF parsing       PyMuPDF
  HTML parsing      Beautiful Soup
  Testing           pytest
  Deployment        Vercel (frontend), Render (backend and database)

## Architecture

``` text
User
 |
 v
React + TypeScript (Vercel)
 |
 | HTTPS / JSON
 v
FastAPI (Render)
 |                 |
 v                 v
Vehicle registry  Quote aggregation
                   |   |   |   |
                   A   B   C   D
                  JSON HTML PDF CSV
                   |
                   v
             Normalized quotes
                   |
                   v
             Plan selection API
                   |
                   v
             PostgreSQL database
```

## Project structure

``` text
autocover/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── selections.py
│   │   ├── core/
│   │   │   ├── database.py
│   │   │   └── init_db.py
│   │   ├── models/
│   │   │   └── plan_selection.py
│   │   ├── providers/
│   │   │   ├── provider_a.py
│   │   │   ├── provider_b.py
│   │   │   ├── provider_c.py
│   │   │   └── provider_d.py
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── quote_aggregator.py
│   │   │   └── selection_service.py
│   │   └── main.py
│   ├── data/              # Supplied registry and provider datasets
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    ├── package.json
    └── vite.config.ts
```

## Run locally

### Prerequisites

-   Python 3.11 (recommended; also used by the backend Docker image)
-   Node.js compatible with the installed Vite version
-   PostgreSQL
-   Git

### 1. Clone the repository

``` bash
git clone https://github.com/abhishekboken12/autocover.git
cd autocover
```

### 2. Create the database

Create a PostgreSQL database named `autocover` and ensure your database
user has permission to connect and create tables.

``` sql
CREATE DATABASE autocover;
```

### 3. Install and configure the backend

``` bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

``` env
DATABASE_URL=postgresql+psycopg://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/autocover
```

Replace the placeholders with your local PostgreSQL credentials. Do not
commit `.env`.

Start the backend from the `backend/` directory:

``` bash
uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`

Swagger UI: `http://127.0.0.1:8000/docs`

Health check: `http://127.0.0.1:8000/health`

Database tables are created when the application starts.

### 4. Install and run the frontend

In a second terminal:

``` bash
cd frontend
npm install
```

For a direct local API URL, create `frontend/.env.local`:

``` env
VITE_API_URL=http://127.0.0.1:8000
```

Then run:

``` bash
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

The Vite development proxy also forwards `/api` and `/health` requests
to the local FastAPI server when relative API paths are used.

## Production deployment

### Backend --- Render

The backend is deployed as a Docker service.

-   Root directory: `backend`
-   Runtime: Docker
-   Dockerfile: `./Dockerfile`
-   Configure `DATABASE_URL` with the Render PostgreSQL connection
    string.
-   The backend normalizes PostgreSQL URL prefixes for the installed
    Psycopg 3 driver.

Production API: `https://autocover.onrender.com`

### Frontend --- Vercel

Configure the Vercel project:

-   Root directory: `frontend`
-   Framework: Vite
-   Build command: `npm run build`
-   Output directory: `dist`

Set this environment variable in Vercel:

``` env
VITE_API_URL=https://autocover.onrender.com
```

Redeploy the frontend after changing environment variables. The FastAPI
CORS configuration must allow the deployed frontend origin.

## API endpoints

  ----------------------------------------------------------------------------------------------------
  Method                  Endpoint                                             Description
  ----------------------- ---------------------------------------------------- -----------------------
  GET                     `/health`                                            Backend health check

  GET                     `/api/providers`                                     List supported
                                                                               providers

  GET                     `/api/vehicles/{registration}`                       Look up vehicle details

  GET                     `/api/quotes/{registration}`                         Compare insurance
                                                                               quotes

  GET                     `/api/quotes/{registration}?quote_date=YYYY-MM-DD`   Compare quotes for a
                                                                               specified date

  POST                    `/api/selections`                                    Save a selected plan

  GET                     `/api/selections/{selection_id}`                     Retrieve a saved
                                                                               selection
  ----------------------------------------------------------------------------------------------------

### Example requests

Vehicle lookup:

``` bash
curl https://autocover.onrender.com/api/vehicles/WB02AB1234
```

Quote comparison:

``` bash
curl https://autocover.onrender.com/api/quotes/WB02AB1234
```

Save a plan:

``` bash
curl -X POST https://autocover.onrender.com/api/selections \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number": "WB02AB1234",
    "provider": "Provider A",
    "plan_name": "Essential",
    "coverage_type": "COMPREHENSIVE",
    "idv": 325000,
    "base_premium": 9965,
    "tax_amount": 1793.70,
    "total_premium": 11758.70
  }'
```

The create response contains the saved selection ID. Use it with
`GET /api/selections/{selection_id}` to retrieve the saved record.

## Quote processing notes

-   Registration numbers are normalized before matching.
-   Provider-specific source formats are parsed into a shared quote
    schema.
-   Monetary values use decimal representations.
-   Expired quotes remain visible in the response but are separated from
    valid quotes.
-   The cheapest quote is selected from the valid quote set.
-   Provider failures are reported separately to support partial
    results.
-   Provider C calculates quotes using the supplied rate card and
    vehicle details, including depreciation, IDV rounding, own-damage
    premium, NCB, third-party premium, add-ons, and GST.
-   Provider C's implementation assumptions should be checked against
    the supplied rate-card source before relying on the calculation.

## Tests and build

Run backend tests from `backend/`:

``` bash
pytest -q
```

Build the frontend from `frontend/`:

``` bash
npm run build
```

## Limitations and disclaimer

-   The application uses the supplied vehicle registry and provider
    datasets. It does not connect to live insurer systems.
-   Quotes are for demonstration and assignment evaluation; they are not
    binding insurance offers.
-   Provider C pricing follows the implemented interpretation of the
    supplied rate card. Review the source rate card and calculation
    assumptions when validating results.
-   Keep all credentials, secrets, and `.env` files out of version
    control.
-   Ensure the supplied provider data files remain available at the
    paths expected by the backend parsers.

## Author

**Abhishek Boken**\
GitHub: [abhishekboken12](https://github.com/abhishekboken12)

------------------------------------------------------------------------

Built as a full-stack vehicle insurance comparison project.
