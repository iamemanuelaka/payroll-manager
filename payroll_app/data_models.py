"""
Modèle de données partagé — postes, calculs, sauvegarde JSON.
"""
from datetime import date, datetime
import copy, json, os

# ── Données par défaut ─────────────────────────────────────────────────────
POSTES_DEFAUT = [
    {"id":1,"nom":"Coordonnateur",                       "sal_min":2_500_000,"quotite":500_000,"date_service":"2007-01-02","max_tranches":5,"duree_tranche":3,"risque":True, "prime_trans":100_000,"prime_comm":150_000},
    {"id":2,"nom":"Coordonnateur Adjoint",               "sal_min":2_000_000,"quotite":400_000,"date_service":"2010-04-12","max_tranches":5,"duree_tranche":3,"risque":True, "prime_trans":100_000,"prime_comm":100_000},
    {"id":3,"nom":"Coord. Composante / Resp. Tech.",     "sal_min":1_750_000,"quotite":350_000,"date_service":"2014-03-13","max_tranches":5,"duree_tranche":3,"risque":False,"prime_trans":100_000,"prime_comm":100_000},
    {"id":4,"nom":"Spécialiste SES",                     "sal_min":1_500_000,"quotite":400_000,"date_service":"2017-02-25","max_tranches":5,"duree_tranche":3,"risque":False,"prime_trans":100_000,"prime_comm":100_000},
    {"id":5,"nom":"Spécialiste",                         "sal_min":1_500_000,"quotite":400_000,"date_service":"2017-02-25","max_tranches":5,"duree_tranche":3,"risque":False,"prime_trans":100_000,"prime_comm":100_000},
    {"id":6,"nom":"Assistant Spécialiste et assimilés",  "sal_min":  800_000,"quotite":166_666,"date_service":"2009-04-12","max_tranches":3,"duree_tranche":2,"risque":False,"prime_trans":100_000,"prime_comm": 50_000},
    {"id":7,"nom":"Assistant SES",                       "sal_min":  800_000,"quotite":166_666,"date_service":"2020-06-18","max_tranches":3,"duree_tranche":2,"risque":False,"prime_trans":100_000,"prime_comm": 50_000},
    {"id":8,"nom":"Assistant comptable / Ass. Direction","sal_min":  500_000,"quotite":100_000,"date_service":"2022-06-02","max_tranches":3,"duree_tranche":2,"risque":False,"prime_trans":100_000,"prime_comm": 50_000},
    {"id":9,"nom":"Chauffeur",                           "sal_min":  250_000,"quotite": 25_000,"date_service":"2001-04-03","max_tranches":5,"duree_tranche":2,"risque":False,"prime_trans":100_000,"prime_comm": 25_000},
]

postes      = copy.deepcopy(POSTES_DEFAUT)
recap_data  = []          # liste de dicts simulation
budget_prevu = 15_000_000
SAVE_FILE   = os.path.join(os.path.expanduser("~"), "payroll_prici_save.json")

# ── Moteur de calcul ───────────────────────────────────────────────────────
def jours_exp(date_str: str) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return max(0, (date.today() - d).days)
    except Exception:
        return 0

def nb_tranches(jours: int, duree_annees, max_t: int) -> int:
    if not duree_annees or duree_annees <= 0:
        return 0
    return min(max_t, int(jours / (duree_annees * 365.25)))

def calculer_salaire(p: dict, date_str: str) -> dict:
    j      = jours_exp(date_str)
    q      = p["quotite"]
    complexite = round(q * 0.25)
    charge     = round(q * 0.05)
    risque_mt  = round(q * 0.05) if p.get("risque") else 0
    tr         = nb_tranches(j, p.get("duree_tranche"), p.get("max_tranches", 0))
    nb_mont    = tr * q
    p_trans    = p.get("prime_trans", 0)
    p_comm     = p.get("prime_comm",  0)
    brut       = p["sal_min"] + nb_mont + complexite + charge + risque_mt
    total      = brut + p_trans + p_comm
    cotis      = round(total * 0.22)
    return {
        "total": total, "brut": brut, "sal_min": p["sal_min"],
        "nb_mont": nb_mont, "complexite": complexite, "charge": charge,
        "risque": risque_mt, "tranches": tr,
        "max_tranches": p.get("max_tranches", 0),
        "duree_tranche": p.get("duree_tranche"),
        "years": int(j / 365.25), "jours": j,
        "prime_trans": p_trans, "prime_comm": p_comm,
        "cotisations": cotis, "net_est": total - cotis,
    }

def fmt(n: float) -> str:
    return f"{int(n):,} F CFA".replace(",", "\u202f")

def int_or(s, default=0) -> int:
    try:
        return int(str(s).replace(" ","").replace("\u202f","").replace("FCFA","").replace(",",""))
    except Exception:
        return default

# ── Persistance ────────────────────────────────────────────────────────────
def sauvegarder(path=None):
    path = path or SAVE_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"postes": postes, "recap": recap_data,
                   "budget": budget_prevu}, f, ensure_ascii=False, indent=2)

def charger(path=None) -> bool:
    global postes, recap_data, budget_prevu
    path = path or SAVE_FILE
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    postes       = data.get("postes",  copy.deepcopy(POSTES_DEFAUT))
    recap_data   = data.get("recap",   [])
    budget_prevu = data.get("budget",  15_000_000)
    return True
