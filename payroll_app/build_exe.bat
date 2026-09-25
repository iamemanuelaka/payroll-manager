@echo off
REM ═══════════════════════════════════════════════════════
REM  BUILD SCRIPT — Payroll Manager PRICI
REM  Lancez ce fichier sur votre machine Windows
REM ═══════════════════════════════════════════════════════

echo Installation des dépendances...
cd /d "%~dp0"
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Génération du .exe (patience ~2-3 minutes)...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "PayrollManager_PRICI" ^
  --add-data "assets;assets" ^
  --add-data "data_models.py;." ^
  --add-data "charts.py;." ^
  --add-data "pdf_generator.py;." ^
  --hidden-import "PySide6.QtCharts" ^
  --hidden-import "matplotlib.backends.backend_qtagg" ^
  --hidden-import "reportlab" ^
  --hidden-import "openpyxl" ^
  main.py

echo.
echo ✓ Terminé ! Votre .exe se trouve dans le dossier dist/
echo   dist\PayrollManager_PRICI.exe
pause
