# Health Prediction Application

A Streamlit app to manage patient blood-test records (Create, Read, Update, Delete) and generate an AI-based
health-risk remark for each patient using the Google Gemini API. Data is stored in SQLite.

## Features
- Full CRUD with search
- Validation: name, email format, DOB (dd/mm/yyyy, real date, not in future), numeric blood values within sane ranges
- Duplicate prevention (unique email, case-insensitive)
- AI remarks via external API; if the API fails the record is saved as "Pending" and can be regenerated from Edit
- No secrets in code: API key is loaded from `.env`

## Project structure
| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI (Add / Records / Edit-Delete) |
| `validators.py` | All input validation rules |
| `database.py` | SQLite CRUD layer |
| `ai_service.py` | Gemini API integration |
| `config.py` | Settings and env loading |
| `tests/` | pytest tests (validators, DB) |

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env        # then add your own GEMINI_API_KEY (free key: https://aistudio.google.com/apikey)
streamlit run app.py
```

## Tests
```bash
python -m pytest -q
```

## Notes
- DOB is accepted as `dd/mm/yyyy`; `.` or `-` separators are normalised to `/` and stored as `dd/mm/yyyy`.
- AI remarks are indicative only and are not a medical diagnosis.
