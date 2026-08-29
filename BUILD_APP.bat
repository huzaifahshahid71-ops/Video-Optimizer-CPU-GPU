@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo        Video Optimizer Studio - Windows Builder
echo ============================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Python 3 was not found.
    pause
    exit /b 1
  )
  set "PY=python"
)

echo [1/6] Installing dependencies...
%PY% -m pip install --upgrade pip
if errorlevel 1 goto :fail
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [2/6] Generating app icon...
%PY% generate_icon.py
if errorlevel 1 goto :fail

echo.
echo [3/6] Running regression tests...
%PY% -m unittest -v test_engine.py
if errorlevel 1 goto :fail

echo.
echo [4/6] Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist VideoOptimizerStudio.spec del /q VideoOptimizerStudio.spec

echo.
echo [5/6] Building one-file EXE...
%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name VideoOptimizerStudio ^
  --icon video_optimizer_studio.ico ^
  --version-file version_info.txt ^
  --add-data "video_optimizer_studio.ico;." ^
  --add-data "video_optimizer_studio_icon.png;." ^
  --collect-all customtkinter ^
  video_optimizer_studio.py
if errorlevel 1 goto :fail

echo.
echo [6/6] Verifying PyInstaller archive...
if not exist "dist\VideoOptimizerStudio.exe" goto :fail
for %%A in ("dist\VideoOptimizerStudio.exe") do set SIZE=%%~zA
if %SIZE% LSS 5000000 (
  echo [ERROR] Built EXE is unexpectedly small: %SIZE% bytes.
  goto :fail
)
%PY% -m PyInstaller.utils.cliutils.archive_viewer -l "dist\VideoOptimizerStudio.exe" >nul
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo BUILD COMPLETE - VERIFIED
echo dist\VideoOptimizerStudio.exe
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed.
pause
exit /b 1
