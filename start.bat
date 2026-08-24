@echo off
cd /d "%~dp0"

if exist venv\Scripts\python.exe (
  venv\Scripts\python.exe -c "import sys" >nul 2>&1
  if errorlevel 1 (
    echo The existing venv is broken. Recreating it...
    rmdir /s /q venv
  )
)

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)

call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Tacob is starting. A browser window should open.
echo If it does not, open http://127.0.0.1:8501
echo.
streamlit run streamlit_app.py --server.headless false --server.port 8501
