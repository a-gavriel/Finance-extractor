@echo off
setlocal
pushd "%~dp0"

set "VENV_DIR=.venv"
set "VENV_SCRIPTS=%VENV_DIR%\Scripts"

if not exist "%VENV_SCRIPTS%\python.exe" (
    echo [INFO] Virtual environment not found. Creating it...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        goto :error
    )
)

call "%VENV_SCRIPTS%\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    goto :error
)

echo [INFO] Installing/updating dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    goto :error
)

echo [INFO] Running email processor...
python src\email_processor.py -g
if errorlevel 1 goto :error

goto :done

:error
echo [ERROR] Script finished with errors.

:done
popd
pause
endlocal