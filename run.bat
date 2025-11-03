@echo off
setlocal

:: Set virtual environment folder
set VENV_DIR=.venv
set VENV_SCRIPTS=%VENV_DIR%\Scripts

:: Check if .venv\Scripts exists
if not exist "%VENV_SCRIPTS%" (
    echo [INFO] Virtual environment not found. Creating it...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

:: Activate the virtual environment
call "%VENV_SCRIPTS%\activate.bat"

:: Install requirements
echo [INFO] Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    exit /b 1
)

:: Run main.py
echo [INFO] Running main.py...
python main.py -g

endlocal
