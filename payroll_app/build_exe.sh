#!/bin/bash
# Script build Linux/Mac (pour générer un binaire natif)
cd "$(dirname "$0")"
pip install -r requirements.txt pyinstaller
pyinstaller \
  --onefile \
  --windowed \
  --name "PayrollManager_PRICI" \
  --add-data "assets:assets" \
  --add-data "data_models.py:." \
  --add-data "charts.py:." \
  --add-data "pdf_generator.py:." \
  --hidden-import "matplotlib.backends.backend_qtagg" \
  main.py
echo "✓ dist/PayrollManager_PRICI prêt"
