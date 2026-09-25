"""
Graphiques matplotlib embarqués dans Qt (FigureCanvasQTAgg).
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

NAVY   = "#FFFFFF"
BLUE   = "#185ABD"
BLUE2  = "#0078D4"
RED    = "#D13438"
GREEN  = "#107C41"
ORANGE = "#CA5010"
GREY   = "#667085"
LIGHT  = "#344054"
BG     = "#FFFFFF"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "axes.edgecolor": "#D0D5DD", "axes.labelcolor": LIGHT,
    "xtick.color": GREY, "ytick.color": GREY,
    "text.color": LIGHT, "grid.color": "#E4E7EC",
    "grid.linewidth": 0.5,
})

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor=BG)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.canvas)
        self.setStyleSheet(f"background:{BG};")

    def _clear(self):
        self.fig.clear()

    def draw_bar_postes(self, noms, totaux, budget_ligne=None):
        self._clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(BG)
        x = np.arange(len(noms))
        colors_bar = [RED if t == max(totaux) else BLUE2 for t in totaux]
        bars = ax.bar(x, [t/1e6 for t in totaux], color=colors_bar,
                      width=0.6, zorder=3, edgecolor="none")
        if budget_ligne:
            ax.axhline(budget_ligne/1e6, color=ORANGE, linestyle="--",
                       linewidth=1.5, label=f"Budget : {budget_ligne/1e6:.1f}M", zorder=4)
            ax.legend(fontsize=8, framealpha=0.2, labelcolor=LIGHT)
        ax.set_xticks(x)
        ax.set_xticklabels([n[:14] for n in noms], rotation=40, ha="right", fontsize=8)
        ax.set_ylabel("Millions F CFA", fontsize=9)
        ax.set_title("Salaire par poste", color=LIGHT, fontsize=11, pad=10)
        ax.yaxis.grid(True, zorder=0)
        ax.set_axisbelow(True)
        self.fig.tight_layout()
        self.canvas.draw()

    def draw_donut(self, noms, totaux):
        self._clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(BG)
        palette = [BLUE2, RED, GREEN, ORANGE, "#9B59B6", "#1ABC9C",
                   "#F1C40F", "#E67E22", "#3498DB"]
        wedge_colors = [palette[i % len(palette)] for i in range(len(noms))]
        wedges, texts, autotexts = ax.pie(
            totaux, colors=wedge_colors, startangle=90,
            wedgeprops={"width": 0.55, "edgecolor": NAVY, "linewidth": 2},
            autopct="%1.1f%%", pctdistance=0.78,
        )
        for at in autotexts:
            at.set_fontsize(8); at.set_color("white")
        short = [n.split("/")[0][:18] for n in noms]
        ax.legend(wedges, short, loc="center left", bbox_to_anchor=(1.0, 0.5),
                  fontsize=8, framealpha=0, labelcolor=LIGHT)
        ax.set_title("Répartition masse salariale", color=LIGHT, fontsize=11, pad=10)
        self.fig.tight_layout()
        self.canvas.draw()

    def draw_budget_vs_reel(self, budget, reel):
        self._clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(BG)
        cats   = ["Budget prévu", "Masse réelle"]
        vals   = [budget/1e6, reel/1e6]
        colors_b = [BLUE2, RED if reel > budget else GREEN]
        bars = ax.bar(cats, vals, color=colors_b, width=0.4,
                      edgecolor="none", zorder=3)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.05,
                    f"{val:.2f}M", ha="center", va="bottom",
                    fontsize=10, color=LIGHT, fontweight="bold")
        ecart = reel - budget
        col   = RED if ecart > 0 else GREEN
        ax.set_title(f"Budget vs Réalisé  (écart : {ecart/1e6:+.2f}M F CFA)",
                     color=col, fontsize=11, pad=10)
        ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
        ax.set_ylabel("Millions F CFA", fontsize=9)
        self.fig.tight_layout()
        self.canvas.draw()

    def draw_evolution(self, mois_labels, valeurs):
        self._clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(BG)
        x = np.arange(len(mois_labels))
        ax.plot(x, [v/1e6 for v in valeurs], color=BLUE2,
                linewidth=2.5, marker="o", markersize=6,
                markerfacecolor=RED, markeredgecolor=NAVY, zorder=3)
        ax.fill_between(x, [v/1e6 for v in valeurs],
                        alpha=0.15, color=BLUE2)
        ax.set_xticks(x); ax.set_xticklabels(mois_labels, fontsize=8)
        ax.set_ylabel("Millions F CFA", fontsize=9)
        ax.set_title("Évolution de la masse salariale", color=LIGHT, fontsize=11, pad=10)
        ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
        self.fig.tight_layout()
        self.canvas.draw()
