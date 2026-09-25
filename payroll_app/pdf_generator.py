"""
Génération de fiches de paie PDF professionnelles avec ReportLab.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os

NAVY  = colors.HexColor("#1F1F1F")
BLUE  = colors.HexColor("#0078D4")
RED   = colors.HexColor("#D13438")
LIGHT = colors.HexColor("#F5F7FA")
GREY  = colors.HexColor("#667085")
WHITE = colors.white
DARK  = colors.HexColor("#344054")
ORANGE= colors.HexColor("#CA5010")

def generer_fiche(poste: dict, result: dict, nom_employe: str,
                  date_service: str, nom_entreprise: str = "PRICI",
                  output_path: str = None) -> str:
    from data_models import fmt
    if output_path is None:
        safe = nom_employe.replace(" ", "_")
        mois = datetime.now().strftime("%Y_%m")
        output_path = os.path.join(os.path.expanduser("~"), f"fiche_{safe}_{mois}.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=12*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()
    story  = []

    # ── En-tête entreprise ─────────────────────────────────────────────
    header_data = [[
        Paragraph(f"<font size='18' color='#FFFFFF'><b>{nom_entreprise}</b></font>", styles["Normal"]),
        Paragraph(f"<font size='10' color='#DCEBFF'>BULLETIN DE PAIE<br/>"
                  f"Période : {datetime.now().strftime('%B %Y').upper()}<br/>"
                  f"Date d'émission : {datetime.now().strftime('%d/%m/%Y')}</font>", styles["Normal"])
    ]]
    t_header = Table(header_data, colWidths=[100*mm, 80*mm])
    t_header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("TEXTCOLOR",  (0,0), (-1,-1), WHITE),
        ("ALIGN",      (1,0), (1,0),   "RIGHT"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("PADDING",    (0,0), (-1,-1), 14),
        ("ROUNDEDCORNERS", [8,8,8,8]),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 6*mm))

    # ── Identité employé ───────────────────────────────────────────────
    style_lbl = ParagraphStyle("lbl", fontSize=9, textColor=GREY)
    style_val = ParagraphStyle("val", fontSize=12, textColor=NAVY, fontName="Helvetica-Bold")
    style_sub = ParagraphStyle("sub", fontSize=10, textColor=BLUE)

    emp_data = [
        [Paragraph("<b>EMPLOYÉ</b>", ParagraphStyle("h",fontSize=9,textColor=GREY)),
         "", "",
         Paragraph("<b>POSTE</b>", ParagraphStyle("h",fontSize=9,textColor=GREY)), ""],
        [Paragraph(f"<b><font size='14'>{nom_employe.upper()}</font></b>", styles["Normal"]),
         "", "",
         Paragraph(poste["nom"], style_sub), ""],
        [Paragraph(f"Date d'entrée : <b>{date_service}</b>", style_lbl),
         "", "",
         Paragraph(f"Ancienneté : <b>{result['years']} ans ({result['jours']} jours)</b>", style_lbl), ""],
        [Paragraph(f"Tranches acquises : <b>{result['tranches']}/{result['max_tranches']}</b>", style_lbl),
         "", "",
         Paragraph(f"Quotité : <b>{fmt(poste['quotite'])}</b>", style_lbl), ""],
    ]
    t_emp = Table(emp_data, colWidths=[70*mm, 5*mm, 5*mm, 80*mm, 20*mm])
    t_emp.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ("ROUNDEDCORNERS", [6,6,6,6]),
        ("PADDING",    (0,0), (-1,-1), 8),
        ("SPAN",       (0,0), (2,0)),
        ("SPAN",       (0,1), (2,1)),
        ("SPAN",       (0,2), (2,2)),
        ("SPAN",       (0,3), (2,3)),
        ("LINEBELOW",  (0,0), (-1,0), 1, colors.HexColor("#DDE1E7")),
    ]))
    story.append(t_emp)
    story.append(Spacer(1, 5*mm))

    # ── Tableau des composantes ────────────────────────────────────────
    story.append(Paragraph("DÉTAIL DES ÉLÉMENTS DE RÉMUNÉRATION",
                            ParagraphStyle("sec", fontSize=10, textColor=BLUE,
                                           fontName="Helvetica-Bold", spaceBefore=4)))
    story.append(Spacer(1, 2*mm))

    rows = [
        ["LIBELLÉ", "BASE", "TAUX / RÈGLE", "MONTANT"],
    ]
    dt = result.get("duree_tranche")
    tr = result["tranches"]
    rows += [
        ["Salaire minimum", "—", "Grille de poste", fmt(result["sal_min"])],
        [f"Tranches d'ancienneté  ({tr} × {fmt(poste['quotite'])})" if dt else "Tranches d'ancienneté",
         f"{tr} tranche(s)" if dt else "—",
         f"{dt} ans/tranche" if dt else "Non applicable",
         fmt(result["nb_mont"])],
        ["Complexité financière", fmt(poste["quotite"]), "25 %", fmt(result["complexite"])],
        ["Charge managériale",    fmt(poste["quotite"]), "5 %",  fmt(result["charge"])],
        ["Risque opérationnel",   fmt(poste["quotite"]) if result["risque"] else "—",
         "5 %" if result["risque"] else "Non applicable", fmt(result["risque"])],
    ]
    rows.append(["SOUS-TOTAL BRUT", "", "", fmt(result["brut"])])
    rows.append(["Prime de transport",    "—", "Forfait", fmt(result["prime_trans"])])
    rows.append(["Prime de communication","—", "Forfait", fmt(result["prime_comm"])])

    col_w = [85*mm, 32*mm, 32*mm, 31*mm]
    t_rows = Table(rows, colWidths=col_w, repeatRows=1)
    row_count = len(rows)
    sub_idx   = row_count - 3   # index SOUS-TOTAL

    ts = [
        ("BACKGROUND",  (0,0), (-1,0),       NAVY),
        ("TEXTCOLOR",   (0,0), (-1,0),        WHITE),
        ("FONTNAME",    (0,0), (-1,0),        "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0),        9),
        ("ALIGN",       (3,0), (3,-1),        "RIGHT"),
        ("ALIGN",       (1,0), (2,-1),        "CENTER"),
        ("FONTSIZE",    (0,1), (-1,-1),        9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F8FC")]),
        ("GRID",        (0,0), (-1,-1),       0.5, colors.HexColor("#DDE1E7")),
        ("PADDING",     (0,0), (-1,-1),        7),
        # Sous-total
        ("BACKGROUND",  (0,sub_idx), (-1,sub_idx), colors.HexColor("#E6F1FB")),
        ("FONTNAME",    (0,sub_idx), (-1,sub_idx), "Helvetica-Bold"),
        ("TEXTCOLOR",   (3,sub_idx), (3,sub_idx),  BLUE),
    ]
    t_rows.setStyle(TableStyle(ts))
    story.append(t_rows)
    story.append(Spacer(1, 5*mm))

    # ── Total et net estimé ────────────────────────────────────────────
    total_data = [
        [Paragraph("<b>SALAIRE TOTAL BRUT</b>",
                   ParagraphStyle("tot", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold")),
         Paragraph(f"<b>{fmt(result['total'])}</b>",
                   ParagraphStyle("totv", fontSize=16, textColor=RED, fontName="Helvetica-Bold",
                                  alignment=TA_RIGHT))],
        [Paragraph("Cotisations estimées (22 %)",
                   ParagraphStyle("cot", fontSize=10, textColor=GREY)),
         Paragraph(f"- {fmt(result['cotisations'])}",
                   ParagraphStyle("cotv", fontSize=10, textColor=ORANGE, alignment=TA_RIGHT))],
        [Paragraph("<b>NET ESTIMÉ À PAYER</b>",
                   ParagraphStyle("net", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold")),
         Paragraph(f"<b>{fmt(result['net_est'])}</b>",
                   ParagraphStyle("netv", fontSize=13, textColor=colors.HexColor("#2ECC71"),
                                  fontName="Helvetica-Bold", alignment=TA_RIGHT))],
    ]
    t_total = Table(total_data, colWidths=[120*mm, 60*mm])
    t_total.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  NAVY),
        ("BACKGROUND",  (0,1), (-1,1),  colors.HexColor("#1A2F4A")),
        ("BACKGROUND",  (0,2), (-1,2),  BLUE),
        ("PADDING",     (0,0), (-1,-1), 12),
        ("LINEABOVE",   (0,0), (-1,0),  2, RED),
    ]))
    story.append(t_total)
    story.append(Spacer(1, 8*mm))

    # ── Pied de page ──────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDE1E7")))
    story.append(Spacer(1, 3*mm))
    footer_style = ParagraphStyle("foot", fontSize=8, textColor=GREY, alignment=TA_CENTER)
    story.append(Paragraph(
        f"Document généré automatiquement par Payroll Manager PRICI · "
        f"{datetime.now().strftime('%d/%m/%Y à %H:%M')} · "
        f"Ce document est confidentiel.", footer_style))
    story.append(Spacer(1, 6*mm))

    # Signatures
    sig_data = [[
        Paragraph("Signature Employé\n\n\n___________________", footer_style),
        Paragraph("Cachet & Signature\nDirection\n\n___________________", footer_style),
    ]]
    t_sig = Table(sig_data, colWidths=[90*mm, 90*mm])
    t_sig.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("PADDING",(0,0),(-1,-1),8)]))
    story.append(t_sig)

    doc.build(story)
    return output_path
