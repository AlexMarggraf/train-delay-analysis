@echo off

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo starting venv
call .venv\Scripts\activate.bat

echo installing requirements
pip install -r requirements.txt

echo starting server
python -m uvicorn main:app --reload
