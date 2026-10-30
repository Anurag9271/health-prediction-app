# Health Prediction Application

A Python application for managing patient blood-test records and generating AI-based health-risk remarks. Built with **Streamlit** (front end), **SQLite** (persistent storage) and the **Google Gemini API** (external AI integration).

> **Disclaimer:** AI-generated remarks are indicative only. They are not a medical diagnosis and must not replace professional medical advice.

---

## Table of Contents

1. [Features](#features)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Prerequisites](#prerequisites)
6. [Installation and Setup](#installation-and-setup)
7. [Running the Application](#running-the-application)
8. [Using the Application](#using-the-application)
9. [Validation Rules](#validation-rules)
10. [Running the Tests](#running-the-tests)
11. [Sample Test Data and Expected Results](#sample-test-data-and-expected-results)
12. [Troubleshooting](#troubleshooting)
13. [Security Notes](#security-notes)

---

## Features

- **Full CRUD**: create, read, update and delete patient records.
- **Search**: filter the record list by name or email.
- **Input validation**: email format, `dd/mm/yyyy` dates, real calendar dates, no future dates of birth, numeric blood values within sensible ranges. All errors are reported together.
- **Duplicate prevention**: email addresses are unique (case-insensitive), enforced by the database.
- **AI integration**: once a record passes validation, patient age and blood values are sent to the Gemini API, and the predicted health risk is saved in the **Remarks** column.
- **Graceful failure**: if the AI service is unavailable, the record is still saved with a "Pending" remark and can be regenerated from the Edit tab.
- **Safe deletion**: deleting requires an explicit confirmation.
- **Automated tests** for validation and database logic.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Front end | Streamlit |
| Database | SQLite (built into Python) |
| AI API | Google Gemini (REST, via `requests`) |
| Configuration | `python-dotenv` |
| Data display | pandas |
| Testing | pytest |

## Project Structure

```
health-prediction-app/
├── app.py                 # Streamlit UI: Add / Records / Edit-Delete pages
├── validators.py          # All input validation rules (no UI or DB code)
├── database.py            # SQLite CRUD layer
├── ai_service.py          # Gemini API integration and error handling
├── config.py              # Settings; loads secrets from environment
├── tests/
│   ├── test_validators.py # Validation tests (incl. assignment test cases)
│   └── test_database.py   # CRUD and duplicate-email tests
├── requirements.txt       # Python dependencies
├── .env.example           # Template for required environment variables
├── .gitignore             # Excludes .env, .venv, *.db, caches
└── README.md
```

## Architecture

```
                 ┌────────────┐
   User input →  │   app.py   │  (Streamlit UI)
                 └─────┬──────┘
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
 ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
 │ validators  │ │  database   │ │  ai_service  │ → Gemini API
 └─────────────┘ └──────┬──────┘ └──────────────┘
                        ▼
                  patients.db (SQLite)
```

**Save flow:** validate input → (if invalid, show all errors and stop) → call the AI API → save to the database → (if the email already exists, show an error and stop) → confirm to the user.

Each module has a single responsibility, so validation, storage and the AI provider can each be changed or tested independently.

## Prerequisites

- **Python 3.10 or newer**. Check with `python --version`.
- **Git**, to clone the repository.
- A free **Gemini API key** from <https://aistudio.google.com/apikey>.
- An internet connection (required for the AI prediction).

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/health-prediction-app.git
cd health-prediction-app
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

| Platform | Command |
|----------|---------|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Your prompt should now start with `(.venv)`.

> If PowerShell blocks activation with an execution-policy error, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the template to a new file named `.env`:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set your own values:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Gemini API key |
| `GEMINI_MODEL` | No | Model name. Change it if the default is retired for your key |
| `DB_PATH` | No | Custom database file location (default: `patients.db` in the project folder) |

The database file and table are created automatically on first launch.

## Running the Application

With the virtual environment active, from the project folder:

```bash
streamlit run app.py
```

Streamlit starts a local server and opens the app in your browser, normally at <http://localhost:8501>. If the browser does not open, copy that address into it manually. Stop the application with `Ctrl + C` in the terminal.

## Using the Application

Use the **Navigation** menu in the sidebar.

| Page | What you can do |
|------|-----------------|
| **Add Patient** | Enter the patient's details and click **Save & Predict**. Valid data is sent to the AI API and the record is saved with its remark. Invalid data shows every error and nothing is saved. |
| **Patient Records** | View all records in a table (including the AI remark) and search by name or email. |
| **Edit / Delete** | Select a record. **Edit** tab: change any field and click **Update Record**. Remarks are regenerated automatically when the date of birth or blood values change, or if you tick *Re-generate AI remarks*. **Delete** tab: tick the confirmation box, then click **Delete Record**. |

**Date entry:** enter dates as `dd/mm/yyyy`. Dots or hyphens as separators (e.g. `28.01.1960`) are accepted and stored as `28/01/1960`.

## Validation Rules

| Field | Rule |
|-------|------|
| Full Name | Required; 2–100 characters; letters, spaces, `.`, `-` and `'` only |
| Date of Birth | Required; `dd/mm/yyyy`; must be a real calendar date; cannot be in the future; not more than 120 years ago |
| Email | Required; valid format (`name@domain.ext`); unique across all records (case-insensitive) |
| Glucose | Required; numeric; 20–800 mg/dL |
| Haemoglobin | Required; numeric; 3–25 g/dL |
| Cholesterol | Required; numeric; 50–600 mg/dL |

The numeric limits are sanity checks to catch typing errors, not clinical thresholds. They can be adjusted in `config.py`.

## Running the Tests

```bash
python -m pytest -q
```

The tests use a temporary database, so your real data is never touched.

## Troubleshooting

| Problem | Likely cause and fix |
|---------|----------------------|
| `streamlit` is not recognised | The virtual environment is not active. Activate it (see step 3), then retry. |
| Remarks show *Pending - AI prediction unavailable* | The AI call failed. The warning message gives the reason. Fix it, then open **Edit / Delete**, select the record and tick *Re-generate AI remarks*. |
| `GEMINI_API_KEY is not configured` | `.env` is missing or the key is empty. Re-check setup step 5 and restart the app. |
| AI error `HTTP 404` | The model name in `.env` is not available for your key. List the models your key supports and set `GEMINI_MODEL` to one of them. |
| AI error `HTTP 400` / `403` | The API key is invalid or has been revoked. Create a new key and update `.env`. |
| AI error `HTTP 429` | Rate or quota limit reached. Wait a minute and retry. |
| AI service timed out | Slow network or VPN. Retry, try another network, or choose a faster (flash-class) model. |
| Changes to `.env` have no effect | Stop the app (`Ctrl + C`) and start it again. |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502`. |
| Want to reset all data | Stop the app and delete `patients.db`; it is recreated on next launch. |

## Security Notes

- API keys are read from environment variables and are **never** committed. `.env` is listed in `.gitignore`.
- The local database (`patients.db`) contains patient data and is also git-ignored.
- All database queries use parameterised statements, which prevents SQL injection.
- Before publishing changes, confirm nothing sensitive is tracked:
  ```bash
  git ls-files          # review the tracked files
  git status            # .env and *.db must not appear
  ```