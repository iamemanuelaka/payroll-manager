# Payroll Manager PRICI

Application de bureau pour simuler, analyser et piloter une masse salariale.
Le projet est construit avec Python, PySide6, Matplotlib, ReportLab et OpenPyXL.

Interface claire inspirée de Microsoft Fluent UI.

## Fonctionnalités

- Simulation du salaire brut et du net estimé par poste.
- Prise en compte de l'ancienneté et des tranches salariales.
- Gestion des primes, de la complexité, de la charge managériale et du risque.
- Récapitulatif des simulations avec export Excel.
- Tableau de bord de masse salariale avec indicateurs et graphiques.
- Modification des paramètres des postes.
- Sauvegarde et chargement des données au format JSON.
- Génération de fiches de paie PDF.
- Interface claire, responsive et inspirée de Microsoft Fluent UI.

## Prérequis

- Python 3.10 ou plus récent.
- Windows, Linux ou macOS.
- Les dépendances listées dans [`payroll_app/requirements.txt`](payroll_app/requirements.txt).

## Installation

```bash
git clone https://github.com/<votre-compte>/payroll-manager-prici.git
cd payroll-manager-prici
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r payroll_app\requirements.txt
python payroll_app\main.py
```

### Linux / macOS

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r payroll_app/requirements.txt
python payroll_app/main.py
```

## Générer un exécutable

Depuis le dossier `payroll_app` :

```bash
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed \
  --name PayrollManager_PRICI \
  --add-data "assets:assets" \
  --hidden-import matplotlib.backends.backend_qtagg \
  main.py
```

Sous Windows, vous pouvez également lancer [`payroll_app/build_exe.bat`](payroll_app/build_exe.bat).

## Accès au tableau de bord

Le tableau de bord de masse salariale est protégé par un raccourci
`Ctrl+Shift+B`. Pour l'activer en local, définissez la variable d'environnement
`PAYROLL_ADMIN_PASSWORD` avant de lancer l'application :

```powershell
$env:PAYROLL_ADMIN_PASSWORD = "votre-mot-de-passe-local"
python payroll_app\main.py
```

Ne committez jamais cette valeur ni vos fichiers de sauvegarde.

## Données locales

L'application conserve sa sauvegarde utilisateur dans
`~/payroll_prici_save.json`. Les sauvegardes JSON, les PDF générés et les
fichiers de build sont exclus du dépôt par [`.gitignore`](.gitignore).

## Structure

```text
payroll_app/
├── assets/style.qss       # Thème clair de l'interface
├── charts.py              # Graphiques Matplotlib intégrés à Qt
├── data_models.py         # Modèle métier et calculs de salaire
├── main.py                # Fenêtre et pages de l'application
├── pdf_generator.py       # Génération des fiches de paie
└── requirements.txt       # Dépendances Python
```

## Vérification rapide

```bash
python -m py_compile payroll_app/main.py payroll_app/charts.py payroll_app/pdf_generator.py
```

## Licence

Ce projet est distribué sous licence MIT. Voir [`LICENSE`](LICENSE).
