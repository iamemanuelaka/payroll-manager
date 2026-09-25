"""
PAYROLL MANAGER PRICI — Application principale PySide6
"""
import sys, os, copy, json
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QScrollArea,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QSpinBox, QCheckBox, QMessageBox,
    QFileDialog, QSplashScreen, QGridLayout, QSizePolicy, QTabWidget,
    QTextEdit, QDoubleSpinBox
)
from PySide6.QtCore  import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, Signal, QThread
from PySide6.QtGui   import QFont, QColor, QPixmap, QPainter, QLinearGradient, QIcon, QKeySequence, QShortcut

import data_models as dm
from data_models  import postes, recap_data, fmt, int_or, calculer_salaire
from charts       import ChartWidget
from datetime     import datetime

# ═══════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ═══════════════════════════════════════════════════════════════════════════
class SplashScreen(QSplashScreen):
    def __init__(self):
        px = QPixmap(600, 380)
        px.fill(QColor("#F5F7FA"))
        painter = QPainter(px)
        # Dégradé de fond
        grad = QLinearGradient(0, 0, 600, 380)
        grad.setColorAt(0, QColor("#F5F7FA"))
        grad.setColorAt(1, QColor("#E8F1FF"))
        painter.fillRect(0, 0, 600, 380, grad)
        # Barre accent
        painter.fillRect(0, 0, 6, 380, QColor("#0078D4"))
        # Titre
        f_title = QFont("Segoe UI", 32, QFont.Bold)
        painter.setFont(f_title)
        painter.setPen(QColor("#1F1F1F"))
        painter.drawText(40, 140, "PAYROLL MANAGER")
        # Sous-titre
        f_sub = QFont("Segoe UI", 14)
        painter.setFont(f_sub)
        painter.setPen(QColor("#0078D4"))
        painter.drawText(40, 175, "Gestion de la masse salariale")
        # Organisation
        f_org = QFont("Segoe UI", 11)
        painter.setFont(f_org)
        painter.setPen(QColor("#667085"))
        painter.drawText(40, 220, "Projet PRICI — Système de simulation & pilotage")
        # Version
        f_ver = QFont("Segoe UI", 9)
        painter.setFont(f_ver)
        painter.setPen(QColor("#98A2B3"))
        painter.drawText(40, 355, "v3.0  ·  © 2025  ·  Confidentiel")
        # Chargement
        painter.setPen(QColor("#0078D4"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(40, 320, "Initialisation en cours…")
        painter.end()
        super().__init__(px)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

# ═══════════════════════════════════════════════════════════════════════════
# WIDGET KPI CARD
# ═══════════════════════════════════════════════════════════════════════════
class KpiCard(QFrame):
    def __init__(self, title, value="—", sub="", color="#D13438", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setMinimumSize(180, 110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        self.lbl_title = QLabel(title); self.lbl_title.setObjectName("kpiTitle")
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;")
        self.lbl_sub   = QLabel(sub);   self.lbl_sub.setObjectName("kpiSub")
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_sub)
        layout.addStretch()

    def update_value(self, val, color=None):
        self.lbl_value.setText(val)
        if color:
            self.lbl_value.setStyleSheet(f"color:{color};font-size:22px;font-weight:bold;")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE SIMULATEUR
# ═══════════════════════════════════════════════════════════════════════════
class SimulateurPage(QWidget):
    simulation_done = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # Titre
        title = QLabel("Simulateur de Salaire")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        sub = QLabel("Calculez le salaire d'un poste en renseignant la date de prise de service.")
        sub.setObjectName("subText"); root.addWidget(sub)

        # Formulaire
        form_frame = QFrame(); form_frame.setObjectName("resultCard")
        form_lay = QGridLayout(form_frame); form_lay.setSpacing(12)
        form_lay.setContentsMargins(20,18,20,18)

        form_lay.addWidget(self._lbl("Nom de l'employé"), 0, 0)
        self.inp_nom = QLineEdit(); self.inp_nom.setPlaceholderText("Ex : Kouassi Ama")
        form_lay.addWidget(self.inp_nom, 1, 0)

        form_lay.addWidget(self._lbl("Poste"), 0, 1)
        self.combo = QComboBox()
        self.combo.addItem("— Sélectionner —")
        for p in postes: self.combo.addItem(p["nom"])
        self.combo.currentIndexChanged.connect(self._on_poste)
        form_lay.addWidget(self.combo, 1, 1)

        form_lay.addWidget(self._lbl("Date de prise de service"), 2, 0)
        self.inp_date = QLineEdit(); self.inp_date.setPlaceholderText("AAAA-MM-JJ")
        self.inp_date.textChanged.connect(self._on_date)
        form_lay.addWidget(self.inp_date, 3, 0)

        form_lay.addWidget(self._lbl("Ancienneté calculée"), 2, 1)
        self.lbl_anc = QLabel("—")
        self.lbl_anc.setStyleSheet("color:#0078D4;font-weight:bold;font-size:14px;padding:8px 12px;")
        form_lay.addWidget(self.lbl_anc, 3, 1)
        root.addWidget(form_frame)

        # Boutons
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self.btn_calc = QPushButton("▶  Calculer le salaire")
        self.btn_calc.setObjectName("primaryBtn")
        self.btn_calc.clicked.connect(self._calculer)
        self.btn_add = QPushButton("＋  Ajouter au récapitulatif")
        self.btn_add.setObjectName("successBtn")
        self.btn_add.clicked.connect(self._enregistrer)
        self.btn_add.setEnabled(False)
        btn_reset = QPushButton("↺  Réinitialiser")
        btn_reset.setObjectName("ghostBtn")
        btn_reset.clicked.connect(self._reset)
        btn_row.addWidget(self.btn_calc)
        btn_row.addWidget(self.btn_add)
        btn_row.addStretch()
        btn_row.addWidget(btn_reset)
        root.addLayout(btn_row)

        # Zone résultat
        self.result_area = QWidget()
        self.result_layout = QVBoxLayout(self.result_area)
        self.result_layout.setContentsMargins(0,0,0,0)
        scroll = QScrollArea(); scroll.setWidget(self.result_area)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.result_area.setStyleSheet("background:transparent;")
        root.addWidget(scroll, stretch=1)
        self._placeholder()

    def _lbl(self, text):
        l = QLabel(text); l.setObjectName("subText"); return l

    def refresh_combo(self):
        cur = self.combo.currentIndex()
        self.combo.clear()
        self.combo.addItem("— Sélectionner —")
        for p in postes: self.combo.addItem(p["nom"])
        self.combo.setCurrentIndex(min(cur, self.combo.count()-1))

    def _on_poste(self, idx):
        if idx > 0 and not self.inp_date.text():
            self.inp_date.setText(postes[idx-1]["date_service"])

    def _on_date(self, text):
        j = dm.jours_exp(text)
        if j > 0:
            y = int(j/365.25)
            self.lbl_anc.setText(f"{y} an{'s' if y>1 else ''}  ({j} jours)")
        else:
            self.lbl_anc.setText("—")

    def _placeholder(self):
        self._clear_result()
        lbl = QLabel("Renseignez le poste et la date, puis cliquez sur « Calculer ».")
        lbl.setObjectName("subText"); lbl.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(lbl)
        self.result_layout.addStretch()

    def _clear_result(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _reset(self):
        self.inp_nom.clear(); self.inp_date.clear()
        self.combo.setCurrentIndex(0); self.lbl_anc.setText("—")
        self._last = None; self.btn_add.setEnabled(False)
        self._placeholder()

    def _calculer(self):
        idx = self.combo.currentIndex()
        if idx <= 0:
            QMessageBox.warning(self, "Champ manquant", "Veuillez sélectionner un poste."); return
        ds = self.inp_date.text().strip()
        try: datetime.strptime(ds, "%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self, "Date invalide", "Format attendu : AAAA-MM-JJ\nEx : 2018-03-15"); return
        p = postes[idx-1]; r = calculer_salaire(p, ds)
        nom = self.inp_nom.text().strip() or "Employé"
        self._last = {"nom": nom, "poste_nom": p["nom"], "poste_idx": idx-1,
                      "date": ds, "result": r,
                      "horodatage": datetime.now().strftime("%d/%m/%Y %H:%M")}
        self.btn_add.setEnabled(True)
        self._afficher(nom, p, r)

    def _afficher(self, nom, p, r):
        self._clear_result()
        card = QFrame(); card.setObjectName("resultCard")
        lay  = QVBoxLayout(card); lay.setSpacing(0); lay.setContentsMargins(0,0,0,0)

        # En-tête
        hdr = QFrame()
        hdr.setStyleSheet("background:#F0F6FF;border-radius:8px 8px 0 0;padding:12px;")
        hdr_lay = QHBoxLayout(hdr); hdr_lay.setContentsMargins(16,12,16,12)
        init = "".join(w[0] for w in nom.split() if w)[:2].upper() or "??"
        av = QLabel(init)
        av.setStyleSheet("background:#0078D4;color:white;font-weight:bold;font-size:15px;"
                         "border-radius:22px;min-width:44px;max-width:44px;min-height:44px;max-height:44px;")
        av.setAlignment(Qt.AlignCenter)
        hdr_lay.addWidget(av)
        info_lay = QVBoxLayout()
        lbl_nom = QLabel(nom); lbl_nom.setStyleSheet("color:#1F1F1F;font-size:15px;font-weight:bold;")
        dt = r["duree_tranche"]; tr = r["tranches"]; mx = r["max_tranches"]
        exp_txt = f"{p['nom']}  ·  {r['years']} an{'s' if r['years']>1 else ''}  ({r['jours']} jours)"
        if dt:
            seuil_next = (tr+1)*dt*365.25
            jours_rest = max(0, int(seuil_next - r["jours"]) + 1)
            next_txt   = f"  ·  Prochaine tranche dans {jours_rest}j" if tr < mx else "  ·  Tranches max atteintes"
            exp_txt   += f"  ·  {tr}/{mx} tranches{next_txt}"
        lbl_sub = QLabel(exp_txt); lbl_sub.setStyleSheet("color:#667085;font-size:11px;")
        info_lay.addWidget(lbl_nom); info_lay.addWidget(lbl_sub)
        hdr_lay.addLayout(info_lay); hdr_lay.addStretch()
        lay.addWidget(hdr)

        # Lignes détail
        body = QWidget(); body_lay = QVBoxLayout(body)
        body_lay.setSpacing(0); body_lay.setContentsMargins(0,0,0,0)
        body.setStyleSheet("background:#FFFFFF;")

        lignes = [
            ("Salaire minimum",                              r["sal_min"],    "#0078D4", True),
        ]
        if dt:
            lignes.append((f"Tranches × Quotité  ({tr} × {fmt(p['quotite'])})",
                           r["nb_mont"], "#0078D4", True))
        lignes += [
            ("Complexité financière  (25 % de la quotité)", r["complexite"], "#344054", True),
            ("Charge managériale  (5 % de la quotité)",     r["charge"],     "#344054", True),
            ("Niveau de risque  (5 % de la quotité)",        r["risque"],    "#D13438" if p.get("risque") else "#98A2B3",
             p.get("risque", False)),
            ("Prime de transport",                           r["prime_trans"],"#CA5010", True),
            ("Prime de communication",                       r["prime_comm"], "#CA5010", True),
        ]
        for i, (lbl_txt, mt, col, actif) in enumerate(lignes):
            row = QFrame()
            row.setStyleSheet(f"background:{'#FFFFFF' if i%2==0 else '#FAFBFC'};padding:2px 0;")
            row_lay = QHBoxLayout(row); row_lay.setContentsMargins(20,7,20,7)
            suffix = "" if actif else "  (non applicable)"
            lbl_ = QLabel(lbl_txt + suffix)
            lbl_.setStyleSheet(f"color:{'#98A2B3' if not actif else '#344054'};font-size:12px;")
            val_ = QLabel(fmt(mt))
            val_.setStyleSheet(f"color:{col if actif else '#98A2B3'};font-size:12px;"
                               f"font-weight:{'bold' if actif else 'normal'};")
            val_.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_lay.addWidget(lbl_); row_lay.addStretch(); row_lay.addWidget(val_)
            body_lay.addWidget(row)

        # Sous-total brut
        sub_row = QFrame(); sub_row.setStyleSheet("background:#F0F6FF;")
        sr_lay = QHBoxLayout(sub_row); sr_lay.setContentsMargins(20,9,20,9)
        QLabel("Sous-total brut  (hors primes)", sr_lay.parent()) # dummy
        l1 = QLabel("Sous-total brut  (hors primes)"); l1.setStyleSheet("color:#667085;font-size:12px;")
        l2 = QLabel(fmt(r["brut"])); l2.setStyleSheet("color:#0078D4;font-weight:bold;font-size:13px;")
        l2.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        sr_lay.addWidget(l1); sr_lay.addStretch(); sr_lay.addWidget(l2)
        body_lay.addWidget(sub_row)
        lay.addWidget(body)

        # Total
        tot_row = QFrame(); tot_row.setObjectName("totalCard")
        tot_row.setStyleSheet("background:#F0F6FF;border:2px solid #9CC2E5;border-radius:0 0 8px 8px;padding:14px 20px;")
        tr_lay = QHBoxLayout(tot_row); tr_lay.setContentsMargins(20,12,20,12)
        lt = QLabel("SALAIRE TOTAL BRUT"); lt.setStyleSheet("color:#344054;font-size:14px;font-weight:bold;")
        vt = QLabel(fmt(r["total"])); vt.setObjectName("bigTotal")
        vt.setStyleSheet("color:#0078D4;font-size:26px;font-weight:bold;")
        vt.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        tr_lay.addWidget(lt); tr_lay.addStretch(); tr_lay.addWidget(vt)
        lay.addWidget(tot_row)

        # Net estimé
        net_row = QFrame()
        net_row.setStyleSheet("background:#ECFDF3;border-radius:0;padding:10px 20px;margin-top:2px;")
        nr_lay  = QHBoxLayout(net_row); nr_lay.setContentsMargins(20,8,20,8)
        ln = QLabel(f"Net estimé à payer  (cotisations 22 % = − {fmt(r['cotisations'])})")
        ln.setStyleSheet("color:#667085;font-size:11px;")
        vn = QLabel(fmt(r["net_est"])); vn.setStyleSheet("color:#107C41;font-size:18px;font-weight:bold;")
        vn.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        nr_lay.addWidget(ln); nr_lay.addStretch(); nr_lay.addWidget(vn)
        lay.addWidget(net_row)

        self.result_layout.addWidget(card)
        self.result_layout.addStretch()
        self.simulation_done.emit(self._last)

    def _enregistrer(self):
        if not self._last:
            QMessageBox.warning(self,"Aucun calcul","Calculez d'abord un salaire."); return
        dm.recap_data.append(copy.deepcopy(self._last))
        QMessageBox.information(self,"Enregistré",
            f"✓ La fiche de {self._last['nom']} a été ajoutée au récapitulatif.")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE RÉCAPITULATIF
# ═══════════════════════════════════════════════════════════════════════════
class RecapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(28,20,28,20); root.setSpacing(12)
        title = QLabel("Récapitulatif des simulations"); title.setObjectName("pageTitle")
        root.addWidget(title)

        # Boutons
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self.btn_del = QPushButton("🗑  Supprimer la sélection"); self.btn_del.setObjectName("dangerBtn")
        self.btn_del.clicked.connect(self._suppr)
        self.btn_vider = QPushButton("🗑  Vider tout"); self.btn_vider.setObjectName("dangerBtn")
        self.btn_vider.clicked.connect(self._vider)
        self.btn_xlsx = QPushButton("📤  Exporter Excel"); self.btn_xlsx.setObjectName("primaryBtn")
        self.btn_xlsx.clicked.connect(self._exporter_xlsx)
        btn_row.addWidget(self.btn_del); btn_row.addWidget(self.btn_vider)
        btn_row.addStretch(); btn_row.addWidget(self.btn_xlsx)
        root.addLayout(btn_row)

        # Table
        cols = ["Horodatage","Nom","Poste","Ancienneté","Tranches",
                "Sal. min","Tranches×Q","Complexité","Charge","Risque",
                "Transport","Communication","Brut","TOTAL"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().hide()
        root.addWidget(self.table, stretch=1)

        # Footer
        self.lbl_total = QLabel("Masse salariale des fiches : —")
        self.lbl_total.setStyleSheet("color:#0078D4;font-weight:bold;font-size:14px;"
                                      "background:#F0F6FF;padding:12px 16px;border-radius:6px;")
        root.addWidget(self.lbl_total)

    def refresh(self):
        self.table.setRowCount(0); masse = 0
        for e in dm.recap_data:
            r = e["result"]; masse += r["total"]
            dt = r.get("duree_tranche")
            row = self.table.rowCount(); self.table.insertRow(row)
            vals = [e["horodatage"], e["nom"], e["poste_nom"],
                    f"{r['years']} ans ({r['jours']}j)",
                    f"{r['tranches']}/{r['max_tranches']}" if dt else "—",
                    fmt(r["sal_min"]), fmt(r["nb_mont"]),
                    fmt(r["complexite"]), fmt(r["charge"]), fmt(r["risque"]),
                    fmt(r["prime_trans"]), fmt(r["prime_comm"]),
                    fmt(r["brut"]), fmt(r["total"])]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if c == len(vals)-1:
                    item.setForeground(QColor("#0078D4"))
                self.table.setItem(row, c, item)
        self.lbl_total.setText(f"Masse salariale des fiches enregistrées : {fmt(masse)}")

    def _suppr(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self,"Aucune sélection","Cliquez sur une ligne."); return
        nom = dm.recap_data[row]["nom"]
        if QMessageBox.question(self,"Confirmer",f"Supprimer la fiche de {nom} ?") == QMessageBox.Yes:
            del dm.recap_data[row]; self.refresh()

    def _vider(self):
        if QMessageBox.question(self,"Confirmer","Vider tout le récapitulatif ?") == QMessageBox.Yes:
            dm.recap_data.clear(); self.refresh()

    def _exporter_xlsx(self):
        try:
            import openpyxl
            from openpyxl.styles import Font as XFont, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.critical(self,"Module manquant","pip install openpyxl"); return
        if not dm.recap_data:
            QMessageBox.warning(self,"Vide","Aucune fiche enregistrée."); return
        path, _ = QFileDialog.getSaveFileName(self,"Exporter Excel","recapitulatif_salaires.xlsx",
                                               "Excel (*.xlsx)")
        if not path: return
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Récapitulatif"
        BHEX="185FA5"; WH="FFFFFF"; AL1="E6F1FB"; AL2="FFFFFF"; TH="F0F7FF"; OH="FAEEDA"
        def S(): return Side(style="thin",color="DDE1E7")
        def B(): return Border(left=S(),right=S(),top=S(),bottom=S())
        headers = ["Horodatage","Nom","Poste","Ancienneté","Tranches","Salaire min",
                   "Tranches×Q","Complexité","Charge","Risque","Transport","Communication","Brut","TOTAL"]
        col_w   = [14,16,28,12,8,15,15,13,12,12,14,13,15,16]
        for c,(h,w) in enumerate(zip(headers,col_w),1):
            cell=ws.cell(1,c,h)
            cell.font=XFont(name="Calibri",bold=True,color=WH)
            cell.fill=PatternFill("solid",start_color=BHEX)
            cell.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
            cell.border=B()
            ws.column_dimensions[openpyxl.utils.get_column_letter(c)].width=w
        ws.row_dimensions[1].height=30
        FMT='#,##0" F CFA"'; masse=0
        for ri,e in enumerate(dm.recap_data,2):
            r=e["result"]; masse+=r["total"]
            bg=AL1 if ri%2==0 else AL2; dt=r.get("duree_tranche")
            vals=[e["horodatage"],e["nom"],e["poste_nom"],
                  f"{r['years']} ans ({r['jours']}j)",
                  f"{r['tranches']}/{r['max_tranches']}" if dt else "—",
                  r["sal_min"],r["nb_mont"],r["complexite"],r["charge"],r["risque"],
                  r["prime_trans"],r["prime_comm"],r["brut"],r["total"]]
            for c,v in enumerate(vals,1):
                bgc=TH if c==14 else OH if c in(11,12) else bg
                cell=ws.cell(ri,c,v)
                cell.fill=PatternFill("solid",start_color=bgc.replace("#",""))
                cell.border=B()
                cell.font=XFont(name="Calibri",size=10,bold=(c==14),color=BHEX if c==14 else "000000")
                cell.alignment=Alignment(horizontal="left" if c in(2,3) else "center",vertical="center")
                if c>=6: cell.number_format=FMT
        rT=len(dm.recap_data)+2
        ws.merge_cells(f"A{rT}:M{rT}")
        tc=ws.cell(rT,1,"MASSE SALARIALE TOTALE")
        tc.font=XFont(name="Calibri",bold=True,color=WH)
        tc.fill=PatternFill("solid",start_color=BHEX)
        tc.alignment=Alignment(horizontal="right",vertical="center"); tc.border=B()
        mc=ws.cell(rT,14,masse)
        mc.font=XFont(name="Calibri",bold=True,size=12,color=WH)
        mc.fill=PatternFill("solid",start_color=BHEX)
        mc.number_format=FMT; mc.alignment=Alignment(horizontal="center",vertical="center"); mc.border=B()
        ws.row_dimensions[rT].height=24; ws.freeze_panes="A2"; ws.sheet_view.showGridLines=False
        wb.save(path)
        QMessageBox.information(self,"Export réussi",f"✓ Fichier exporté :\n{path}")

# ═══════════════════════════════════════════════════════════════════════════
# PAGE PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════
class ParamsPage(QWidget):
    params_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vars = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(28,20,28,20); root.setSpacing(12)
        title = QLabel("Paramètres des postes"); title.setObjectName("pageTitle")
        root.addWidget(title)
        info = QLabel("ℹ  Modifiez les paramètres puis cliquez sur « Appliquer ».")
        info.setStyleSheet("color:#185ABD;background:#E8F1FF;padding:8px 12px;border-radius:6px;")
        root.addWidget(info)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        grid  = QGridLayout(inner); grid.setSpacing(12); grid.setContentsMargins(0,0,12,0)
        COLS  = 2
        for i, p in enumerate(postes):
            r, c = divmod(i, COLS)
            card  = self._make_card(p)
            grid.addWidget(card, r, c)
        for c in range(COLS): grid.setColumnStretch(c, 1)
        scroll.setWidget(inner); root.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_reset = QPushButton("↺  Réinitialiser"); btn_reset.setObjectName("ghostBtn")
        btn_reset.clicked.connect(self._reset)
        btn_apply = QPushButton("✓  Appliquer"); btn_apply.setObjectName("primaryBtn")
        btn_apply.clicked.connect(self._apply)
        self.lbl_ok = QLabel("")
        self.lbl_ok.setStyleSheet("color:#107C41;font-weight:bold;")
        btn_row.addWidget(btn_reset); btn_row.addWidget(btn_apply)
        btn_row.addWidget(self.lbl_ok); btn_row.addStretch()
        root.addLayout(btn_row)

    def _make_card(self, p):
        card = QFrame(); card.setObjectName("resultCard")
        lay  = QVBoxLayout(card); lay.setSpacing(8); lay.setContentsMargins(14,12,14,14)
        # Header
        hdr = QFrame(); hdr.setStyleSheet("background:#F0F6FF;border-radius:6px;padding:6px 10px;")
        hl  = QHBoxLayout(hdr); hl.setContentsMargins(10,6,10,6)
        badge = QLabel(f" {p['id']} ")
        badge.setStyleSheet("background:#D13438;color:white;font-weight:bold;border-radius:4px;padding:2px 6px;")
        nom_lbl = QLabel(p["nom"]); nom_lbl.setStyleSheet("color:#185ABD;font-weight:bold;")
        hl.addWidget(badge); hl.addWidget(nom_lbl); hl.addStretch()
        lay.addWidget(hdr)

        vs = {}; self._vars[p["id"]] = vs

        def field(label, key, val):
            fl = QHBoxLayout(); fl.setSpacing(8)
            lbl_w = QLabel(label); lbl_w.setObjectName("subText"); lbl_w.setFixedWidth(190)
            inp   = QLineEdit(str(val))
            inp.setStyleSheet("color:#185ABD;font-weight:bold;text-align:right;")
            fl.addWidget(lbl_w); fl.addWidget(inp)
            lay.addLayout(fl); vs[key] = inp

        field("Salaire minimum (F CFA)", "sal_min",    p["sal_min"])
        field("Quotité (F CFA)",          "quotite",    p["quotite"])
        field("Prime transport (F CFA)",  "prime_trans",p.get("prime_trans",0))
        field("Prime communication (F CFA)","prime_comm",p.get("prime_comm",0))

        # Tranches
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#D0D5DD;"); lay.addWidget(sep)
        t_row = QHBoxLayout(); t_row.setSpacing(8)
        t_row.addWidget(QLabel("Durée/tranche (ans) :"))
        vd = QLineEdit(str(p["duree_tranche"]) if p.get("duree_tranche") else "")
        vd.setFixedWidth(50); vd.setStyleSheet("color:#185ABD;font-weight:bold;")
        t_row.addWidget(vd); vs["duree_tranche"] = vd
        t_row.addWidget(QLabel("  Max tranches :"))
        vm = QLineEdit(str(p["max_tranches"])); vm.setFixedWidth(50)
        vm.setStyleSheet("color:#185ABD;font-weight:bold;")
        t_row.addWidget(vm); vs["max_tranches"] = vm
        t_row.addStretch(); lay.addLayout(t_row)

        # Risque
        chk = QCheckBox("Niveau de risque applicable (5 % de la quotité)")
        chk.setChecked(bool(p.get("risque",False)))
        chk.setStyleSheet("color:#D13438;")
        vs["risque"] = chk; lay.addWidget(chk)
        return card

    def _apply(self):
        try:
            for p in postes:
                vs = self._vars[p["id"]]
                p["sal_min"]      = int_or(vs["sal_min"].text())
                p["quotite"]      = int_or(vs["quotite"].text())
                p["prime_trans"]  = int_or(vs["prime_trans"].text())
                p["prime_comm"]   = int_or(vs["prime_comm"].text())
                p["max_tranches"] = int_or(vs["max_tranches"].text(), 3)
                p["risque"]       = vs["risque"].isChecked()
                dt = vs["duree_tranche"].text().strip()
                p["duree_tranche"] = int(dt) if dt else None
                if p["sal_min"] <= 0 or p["quotite"] <= 0:
                    raise ValueError(f"Poste {p['id']} : montants > 0 requis")
            self.lbl_ok.setText("✓ Appliqué"); QTimer.singleShot(2500, lambda: self.lbl_ok.setText(""))
            self.params_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self,"Erreur",str(ex))

    def _reset(self):
        global postes
        dm.postes[:] = copy.deepcopy(dm.POSTES_DEFAUT)
        self.params_changed.emit()
        # Reconstruire
        self._vars = {}
        root = self.layout()
        scroll = root.itemAt(3).widget()
        inner = scroll.widget()
        grid  = inner.layout()
        while grid.count():
            item = grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        COLS = 2
        for i, p in enumerate(postes):
            r, c = divmod(i, COLS)
            grid.addWidget(self._make_card(p), r, c)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE DASHBOARD (Masse Salariale — secrète)
# ═══════════════════════════════════════════════════════════════════════════
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._eff_inputs = {}
        self._build()

    def _build(self):
        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Panneau gauche (effectifs) ─────────────────────────────────
        left = QFrame(); left.setFixedWidth(280)
        left.setStyleSheet("background:#FFFFFF;border-right:1px solid #E1E5EA;")
        ll = QVBoxLayout(left); ll.setContentsMargins(16,20,16,16); ll.setSpacing(10)
        lbl_eff = QLabel("Effectifs par poste"); lbl_eff.setObjectName("sectionTitle")
        ll.addWidget(lbl_eff)
        info = QLabel("Saisissez le nombre d'employés par catégorie.")
        info.setWordWrap(True); info.setObjectName("subText"); ll.addWidget(info)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        il = QVBoxLayout(inner); il.setSpacing(6)
        for p in postes:
            row = QHBoxLayout()
            lbl = QLabel(p["nom"][:22]); lbl.setObjectName("subText"); lbl.setWordWrap(True)
            sp  = QSpinBox(); sp.setRange(0, 9999); sp.setValue(1)
            sp.setFixedWidth(70)
            sp.setStyleSheet("color:#185ABD;font-weight:bold;")
            sp.valueChanged.connect(self._refresh_metrics)
            self._eff_inputs[p["id"]] = sp
            row.addWidget(lbl, stretch=1); row.addWidget(sp)
            il.addLayout(row)
        il.addStretch(); scroll.setWidget(inner); ll.addWidget(scroll)

        btn_budget = QPushButton("⚙  Modifier le budget prévu")
        btn_budget.setObjectName("ghostBtn"); btn_budget.clicked.connect(self._edit_budget)
        ll.addWidget(btn_budget)
        root.addWidget(left)

        # ── Panneau droit (dashboard) ──────────────────────────────────
        right = QWidget(); right.setStyleSheet("background:#F5F7FA;")
        rl = QVBoxLayout(right); rl.setContentsMargins(24,20,24,20); rl.setSpacing(14)

        # Titre
        th = QHBoxLayout()
        title = QLabel("Masse Salariale — Tableau de bord"); title.setObjectName("pageTitle")
        lbl_date = QLabel(datetime.now().strftime("%B %Y").upper())
        lbl_date.setStyleSheet("color:#0078D4;font-size:12px;")
        th.addWidget(title); th.addStretch(); th.addWidget(lbl_date)
        rl.addLayout(th)

        # KPIs
        kpi_grid = QGridLayout(); kpi_grid.setSpacing(12)
        self.kpi_masse   = KpiCard("Masse salariale mensuelle", "—", "Mois en cours", "#D13438")
        self.kpi_annuel  = KpiCard("Masse salariale annuelle",  "—", "× 12", "#D13438")
        self.kpi_moy     = KpiCard("Coût moyen / employé",      "—", "Mois en cours", "#0078D4")
        self.kpi_eff     = KpiCard("Effectif total",             "—", "Mois en cours", "#0078D4")
        self.kpi_budget  = KpiCard("Budget prévu / mois",        fmt(dm.budget_prevu), "", "#CA5010")
        self.kpi_ecart   = KpiCard("Écart Budget vs Réalisé",    "—", "", "#107C41")
        for i, k in enumerate([self.kpi_masse, self.kpi_annuel, self.kpi_moy,
                                self.kpi_eff,  self.kpi_budget, self.kpi_ecart]):
            kpi_grid.addWidget(k, i//3, i%3)
        rl.addLayout(kpi_grid)

        # Graphiques en onglets
        tabs = QTabWidget()
        self.chart_bar    = ChartWidget()
        self.chart_donut  = ChartWidget()
        self.chart_budget = ChartWidget()
        tabs.addTab(self.chart_bar,    "  Salaires par poste  ")
        tabs.addTab(self.chart_donut,  "  Répartition  ")
        tabs.addTab(self.chart_budget, "  Budget vs Réalisé  ")
        rl.addWidget(tabs, stretch=1)

        root.addWidget(right, stretch=1)

    def refresh(self):
        self._refresh_metrics()

    def _refresh_metrics(self):
        total_masse = 0; total_agents = 0
        noms=[]; totaux=[]
        for p in postes:
            cnt = self._eff_inputs[p["id"]].value()
            r   = calculer_salaire(p, p["date_service"])
            cout = r["total"] * cnt
            total_masse  += cout; total_agents += cnt
            noms.append(p["nom"]); totaux.append(r["total"])
        sal_moy = total_masse / total_agents if total_agents else 0
        ecart   = total_masse - dm.budget_prevu
        self.kpi_masse.update_value(fmt(total_masse),"#D13438")
        self.kpi_annuel.update_value(fmt(total_masse*12),"#D13438")
        self.kpi_moy.update_value(fmt(sal_moy) if total_agents else "—","#0078D4")
        self.kpi_eff.update_value(str(total_agents),"#0078D4")
        self.kpi_budget.update_value(fmt(dm.budget_prevu),"#CA5010")
        col   = "#D13438" if ecart > 0 else "#107C41"
        prefix= "+" if ecart > 0 else ""
        self.kpi_ecart.update_value(f"{prefix}{fmt(ecart)}",col)
        # Graphiques
        self.chart_bar.draw_bar_postes(noms, totaux, dm.budget_prevu)
        self.chart_donut.draw_donut(noms, totaux)
        self.chart_budget.draw_budget_vs_reel(dm.budget_prevu, total_masse)

    def _edit_budget(self):
        dlg = QDialog(self); dlg.setWindowTitle("Modifier le budget mensuel prévu")
        dlg.setStyleSheet(self.styleSheet())
        lay = QFormLayout(dlg); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        inp = QLineEdit(str(dm.budget_prevu)); inp.setObjectName("primaryBtn")
        inp.setStyleSheet("color:#185ABD;font-size:14px;font-weight:bold;padding:8px;")
        lay.addRow("Budget prévu (F CFA) :", inp)
        btn = QPushButton("Appliquer"); btn.setObjectName("primaryBtn")
        def _apply():
            v = int_or(inp.text())
            if v > 0: dm.budget_prevu = v; self.kpi_budget.update_value(fmt(v),"#CA5010"); self._refresh_metrics(); dlg.accept()
        btn.clicked.connect(_apply); lay.addRow(btn); dlg.exec()

# ═══════════════════════════════════════════════════════════════════════════
# FENÊTRE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Payroll Manager PRICI")
        self.resize(1280, 820); self.setMinimumSize(1080, 680)
        self._secret_unlocked = False

        # Charger QSS
        qss_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        dm.charger()
        self._build_ui()
        self._setup_shortcuts()
        self.protocol_close()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_lay = QHBoxLayout(central); main_lay.setContentsMargins(0,0,0,0); main_lay.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(200)
        sb_lay  = QVBoxLayout(sidebar); sb_lay.setContentsMargins(0,0,0,0); sb_lay.setSpacing(0)

        title_lbl = QLabel("PAYROLL"); title_lbl.setObjectName("sidebarTitle")
        sub_lbl   = QLabel("Manager PRICI"); sub_lbl.setObjectName("sidebarSub")
        sb_lay.addWidget(title_lbl); sb_lay.addWidget(sub_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator"); sep.setFixedHeight(1)
        sb_lay.addWidget(sep)

        self._nav_btns = {}
        nav_items = [
            ("sim",    "📋  Simulateur"),
            ("recap",  "📊  Récapitulatif"),
            ("params", "⚙   Paramètres"),
        ]
        for key, label in nav_items:
            btn = QPushButton(label); btn.setObjectName("navBtn"); btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=key: self._nav(k))
            sb_lay.addWidget(btn); self._nav_btns[key] = btn

        sb_lay.addStretch()

        # Boutons bas sidebar
        btn_save = QPushButton("💾  Sauvegarder"); btn_save.setObjectName("ghostBtn")
        btn_save.clicked.connect(self._sauvegarder_ui)
        btn_load = QPushButton("📂  Charger");     btn_load.setObjectName("ghostBtn")
        btn_load.clicked.connect(self._charger_ui)
        sb_lay.addWidget(btn_save); sb_lay.addWidget(btn_load)
        sb_lay.addSpacing(12)
        main_lay.addWidget(sidebar)

        # ── Stack de pages ─────────────────────────────────────────────
        content = QFrame(); content.setObjectName("contentArea")
        cl = QVBoxLayout(content); cl.setContentsMargins(0,0,0,0)
        self.stack = QStackedWidget()
        self.page_sim    = SimulateurPage()
        self.page_recap  = RecapPage()
        self.page_params = ParamsPage()
        self.page_dash   = DashboardPage()
        self.stack.addWidget(self.page_sim)     # 0
        self.stack.addWidget(self.page_recap)   # 1
        self.stack.addWidget(self.page_params)  # 2
        self.stack.addWidget(self.page_dash)    # 3
        cl.addWidget(self.stack)
        main_lay.addWidget(content, stretch=1)

        # Connexions
        self.page_params.params_changed.connect(self.page_sim.refresh_combo)
        self.page_params.params_changed.connect(self.page_dash.refresh)

        self._nav("sim")

    def _nav(self, key):
        mapping = {"sim": 0, "recap": 1, "params": 2, "dash": 3}
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        idx = mapping.get(key, 0)
        self.stack.setCurrentIndex(idx)
        if key == "recap":  self.page_recap.refresh()
        if key == "params": pass
        if key == "dash":   self.page_dash.refresh()

    def _setup_shortcuts(self):
        sc = QShortcut(QKeySequence("Ctrl+Shift+B"), self)
        sc.activated.connect(self._unlock_secret)

    def _unlock_secret(self):
        if self._secret_unlocked: self._nav("dash"); return
        from PySide6.QtWidgets import QInputDialog
        pwd, ok = QInputDialog.getText(self, "Accès restreint",
                                       "Mot de passe administrateur :", QLineEdit.Password)
        admin_password = os.environ.get("PAYROLL_ADMIN_PASSWORD", "")
        if ok and admin_password and pwd == admin_password:
            self._secret_unlocked = True
            if "dash" not in self._nav_btns:
                btn = QPushButton("🔒  Masse Salariale"); btn.setObjectName("navBtn"); btn.setCheckable(True)
                btn.clicked.connect(lambda: self._nav("dash"))
                # Insérer avant le stretch
                sb = self.centralWidget().layout().itemAt(0).widget()
                sb_lay = sb.layout()
                sb_lay.insertWidget(sb_lay.count()-3, btn)
                self._nav_btns["dash"] = btn
            QMessageBox.information(self,"Déverrouillé","Module de pilotage de masse salariale activé.\n(Ctrl+Shift+B)")
            self._nav("dash")
        elif ok and not admin_password:
            QMessageBox.warning(
                self,
                "Configuration requise",
                "Définissez la variable PAYROLL_ADMIN_PASSWORD pour activer cet accès.",
            )
        elif ok:
            QMessageBox.critical(self,"Refusé","Mot de passe incorrect.")

    def _sauvegarder_ui(self):
        path, _ = QFileDialog.getSaveFileName(self,"Sauvegarder","sauvegarde_payroll.json",
                                               "JSON (*.json)")
        if not path: return
        try:
            dm.sauvegarder(path); dm.sauvegarder()
            QMessageBox.information(self,"Sauvegardé",f"✓ Sauvegarde réussie :\n{path}")
        except Exception as ex:
            QMessageBox.critical(self,"Erreur",str(ex))

    def _charger_ui(self):
        path, _ = QFileDialog.getOpenFileName(self,"Charger une sauvegarde","","JSON (*.json)")
        if not path: return
        try:
            dm.charger(path)
            self.page_sim.refresh_combo(); self.page_recap.refresh()
            QMessageBox.information(self,"Chargé","✓ Données chargées.")
        except Exception as ex:
            QMessageBox.critical(self,"Erreur",str(ex))

    def protocol_close(self):
        pass

    def closeEvent(self, event):
        try: dm.sauvegarder()
        except Exception: pass
        event.accept()

# ═══════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Payroll Manager PRICI")
    app.setStyle("Fusion")

    # Splash
    splash = SplashScreen()
    splash.show(); app.processEvents()

    win = MainWindow()
    QTimer.singleShot(2200, lambda: (splash.finish(win), win.show()))
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
