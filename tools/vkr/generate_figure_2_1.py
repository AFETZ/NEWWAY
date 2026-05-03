#!/usr/bin/env python3
"""Generate Figure 2.1 — Architecture of the co-simulation environment.

Creates a publication-quality architecture block-diagram for VKR chapter 2,
section 2.2.3.  Output: archive/2026-05-03/vkr_manuscript/figures/figure_2_1_architecture.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── colour palette (neutral, academic) ──────────────────────────────
C_APP   = "#d5e8d4"   # green-tint – application layer
C_ETSI  = "#dae8fc"   # blue-tint  – ETSI Facilities
C_NET   = "#e1d5e7"   # violet-tint – network/transport
C_PHY   = "#fff2cc"   # yellow-tint – PHY + channel
C_SUMO  = "#f8cecc"   # red-tint   – SUMO
C_ART   = "#f5f5f5"   # light grey – artefact boxes
C_ARROW = "#333333"
C_BORDER = "#999999"

def draw():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # ── helper: rounded rectangle with text ──────────────────────────
    def box(x, y, w, h, text, fc, fontsize=9, bold=False, ha="center"):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.15",
            facecolor=fc, edgecolor=C_BORDER, linewidth=1.2,
        )
        ax.add_patch(rect)
        weight = "bold" if bold else "normal"
        ax.text(x + w / 2, y + h / 2, text,
                ha=ha if ha != "center" else "center", va="center",
                fontsize=fontsize, fontweight=weight, wrap=True)

    def small_box(x, y, w, h, text, fc=C_ART, fs=7.5):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08",
            facecolor=fc, edgecolor="#bbb", linewidth=0.8,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text,
                ha="center", va="center", fontsize=fs,
                fontfamily="monospace")

    def arrow(x1, y1, x2, y2, text="", bidirectional=False, color=C_ARROW):
        style = "<->" if bidirectional else "->"
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color,
                                    lw=1.8, connectionstyle="arc3,rad=0"))
        if text:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx, my + 0.15, text, ha="center", va="bottom",
                    fontsize=7.5, color="#555", style="italic")

    # ── Layer 1: Application (top) ───────────────────────────────────
    box(0.5, 8.3, 13, 1.4, "", C_APP)
    ax.text(7, 9.45, "Прикладной уровень", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.text(7, 9.05, "emergencyVehicleAlert  (CAM / DENM / CPM  →  решение  →  маневр)",
            ha="center", va="center", fontsize=9)

    # artefact boxes inside app layer
    small_box(1.0, 8.45, 2.0, 0.45, "MSG.csv")
    small_box(3.3, 8.45, 2.0, 0.45, "CTRL.csv")
    small_box(5.6, 8.45, 2.2, 0.45, "PROFILE.csv")
    small_box(8.1, 8.45, 2.5, 0.45, "collision.xml")
    small_box(10.9, 8.45, 2.2, 0.45, "netstate.xml")

    # ── Layer 2: ETSI Facilities ─────────────────────────────────────
    box(0.5, 6.8, 13, 1.2, "", C_ETSI)
    ax.text(7, 7.65, "ETSI Facilities Layer", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.text(7, 7.2, "CA Basic Service  |  DEN Basic Service  |  CP Basic Service  |  LDM  |  VDP",
            ha="center", va="center", fontsize=9)

    # ── Layer 3: Network / Transport ─────────────────────────────────
    box(0.5, 5.4, 13, 1.1, "", C_NET)
    ax.text(7, 6.2, "Сетевой и транспортный уровни", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.text(7, 5.8, "BTP  |  GeoNetworking  |  DCC (адаптивный / реактивный)",
            ha="center", va="center", fontsize=9)

    # ── Layer 4: PHY + Channel ───────────────────────────────────────
    box(0.5, 3.4, 13, 1.7, "", C_PHY)
    ax.text(7, 4.85, "Канальный и физический уровни", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.text(7, 4.45, "IEEE 802.11p  |  LTE-V2X Mode 4  |  NR-V2X Mode 2",
            ha="center", va="center", fontsize=9)
    # Sionna box inside PHY
    box(2.5, 3.55, 9, 0.65, "Sionna RT  (GPU ray-tracing)  /  статистическая модель канала",
        "#ffe0b2", fontsize=9)

    # ── Layer 5: SUMO ────────────────────────────────────────────────
    box(0.5, 1.2, 13, 1.85, "", C_SUMO)
    ax.text(7, 2.8, "Транспортный симулятор  (SUMO)", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.text(7, 2.3, "TraCI  ↔  ns-3:  координаты, скорости, полосы, инцидент",
            ha="center", va="center", fontsize=9)
    small_box(3.0, 1.35, 2.5, 0.5, "netstate.xml")
    small_box(6.0, 1.35, 2.5, 0.5, "collision.xml")
    small_box(9.0, 1.35, 3.5, 0.5, "route / net files")

    # ── Inter-layer arrows ───────────────────────────────────────────
    # SUMO <-> PHY (via ns-3)
    arrow(3.0, 3.15, 3.0, 3.4, "", bidirectional=True)
    arrow(7.0, 3.15, 7.0, 3.4, "", bidirectional=True)
    arrow(11.0, 3.15, 11.0, 3.4, "", bidirectional=True)

    # Annotations for bidirectional exchange
    ax.text(0.3, 3.25, "SUMO → ns-3:\nкоординаты,\nскорости",
            fontsize=7, color="#666", va="center")
    ax.text(13.7, 3.25, "ns-3 → SUMO:\nslowDown,\nchangeLane",
            fontsize=7, color="#666", va="center", ha="right")

    # PHY <-> NET
    arrow(7.0, 5.1, 7.0, 5.4, "", bidirectional=True)

    # NET <-> ETSI
    arrow(7.0, 6.5, 7.0, 6.8, "", bidirectional=True)

    # ETSI <-> APP
    arrow(7.0, 8.0, 7.0, 8.3, "", bidirectional=True)

    # Sionna <-> outside (GPU)
    ax.annotate("ns-3 ↔ Sionna RT:\nкоординаты ТС →\npath loss, CIR",
                xy=(12.8, 3.87), xytext=(12.8, 2.0),
                fontsize=7, color="#e65100", ha="center",
                arrowprops=dict(arrowstyle="<->", color="#e65100",
                                lw=1.5, connectionstyle="arc3,rad=0"))

    # ── Title ────────────────────────────────────────────────────────
    ax.text(7, 0.15,
            "Рисунок 2.1 — Архитектура инструментальной среды совместного моделирования",
            ha="center", va="bottom", fontsize=10, fontweight="bold")

    fig.tight_layout()
    out_path = OUT_DIR / "figure_2_1_architecture.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    draw()
