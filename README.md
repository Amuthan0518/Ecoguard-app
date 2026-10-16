# EcoGuard Starter

A beginner-friendly Python + Streamlit environmental education app.

## Features
- Climate lessons
- Eco quiz and points
- Daily challenges
- Simplified carbon emissions calculator
- Tree planting tracker
- Live weather and 5-day forecast (city search or browser location permission)
- Offline keyword-based Eco Assistant

## Requirements
- Python 3.10–3.14
- Internet access for the first package installation

## Setup (Windows)
1. Install Python from https://www.python.org/downloads/ . During installation, enable **Add Python to PATH** if that option appears.
2. Extract this ZIP file.
3. Open Command Prompt or PowerShell inside the extracted `ecoguard_starter` folder.
4. Create a virtual environment:

   `python -m venv .venv`

5. Activate it in Command Prompt:

   `.venv\Scripts\activate.bat`

   Or PowerShell:

   `.venv\Scripts\Activate.ps1`

6. Install dependencies:

   `python -m pip install -r requirements.txt`

7. Start EcoGuard:

   `python -m streamlit run app.py`

8. Open the local URL shown in the terminal (usually http://localhost:8501).

## Setup (macOS / Linux)
1. Open a terminal in this folder.
2. Run:

   `python3 -m venv .venv`

   `source .venv/bin/activate`

   `python -m pip install -r requirements.txt`

   `python -m streamlit run app.py`

## Data storage
The app creates `ecoguard.db` in the same folder when it runs. Keep that file if you want to keep locally saved points and tree records. Do not upload a database containing personal information to a public repository.

## Weather feature
- Requires internet access. City search uses Open-Meteo geocoding and forecast APIs.
- Browser location is optional and only works if the user grants permission; city search is the fallback.
- Check Open-Meteo terms and attribution requirements before commercial deployment.

## Important limitations
- The carbon calculator uses editable example factors and is not a formal emissions audit. Replace factors with trusted regional data before presenting results as accurate.
- The Eco Assistant is keyword-based, not a real AI model yet.
- This starter has no accounts or multi-user separation. A deployed public version needs proper authentication, per-user data isolation, validation, privacy protections, and deployment configuration.
- The local SQLite database may not be suitable for every cloud hosting setup. Choose persistent storage before launching publicly.

## Suggested next steps
1. Test all six sections.
2. Add unit tests and better input validation.
3. Separate app logic into modules.
4. Build a FastAPI backend and expose safe API endpoints.
5. Connect a mobile app to that API.
6. Add a real AI provider only after reviewing API costs, privacy and secret-key handling. Never place API keys in mobile app code or commit them to Git.
