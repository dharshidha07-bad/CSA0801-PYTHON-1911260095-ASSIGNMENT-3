"""Draw every graph and diagram used in the report (matplotlib only)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)


def load(q):
    with open(os.path.join(ROOT, q, "results.json")) as f:
        return json.load(f)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=150)
    plt.close(fig)


def box(ax, x, y, w, h, text, fc="#e8f1fb", ec="#2c5d8f", fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, color="#444"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, color=color, lw=1.1))


def line_plot(data, xkey, series, title, name, ylabel="time (s)", xlabel="n"):
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    for key, label in series:
        ax.plot([d[xkey] for d in data], [d[key] for d in data], marker="o", label=label)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title, fontsize=10)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    save(fig, name)


def make_all():
    # ---------------- Q1
    r = load("Q1")
    line_plot(r["timing"], "n", [("naive", "naive (re-add window)"), ("running", "running sum"),
                                 ("deque", "deque + running sum")],
              "Q1: 7-day moving average (log-log)", "q1_timing.png")

    # ---------------- Q2 memory diagram
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax in axes:
        ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax = axes[0]
    ax.set_title("[[0] * 3] * 3   (the bug)", fontsize=10)
    box(ax, 0.2, 2.4, 1.2, 1.0, "grid", fc="#fff3cd", ec="#a07800")
    for i in range(3):
        box(ax, 2.4, 4.2 - 1.5 * i, 1.4, 0.9, f"outer[{i}]")
        arrow(ax, (1.4, 2.9), (2.4, 4.65 - 1.5 * i))
        arrow(ax, (3.8, 4.65 - 1.5 * i), (6.0, 3.0))
    box(ax, 6.0, 2.4, 3.6, 1.2, "ONE list object\n[0, 0, 0]", fc="#fde2e2", ec="#b00020")
    ax.text(5, 0.3, "all three rows are the same object:\nbad[0] is bad[1] -> True", ha="center", fontsize=8)
    ax = axes[1]
    ax.set_title("[[0] * 3 for _ in range(3)]   (correct)", fontsize=10)
    box(ax, 0.2, 2.4, 1.2, 1.0, "grid", fc="#fff3cd", ec="#a07800")
    for i in range(3):
        box(ax, 2.4, 4.2 - 1.5 * i, 1.4, 0.9, f"outer[{i}]")
        arrow(ax, (1.4, 2.9), (2.4, 4.65 - 1.5 * i))
        box(ax, 6.0, 4.2 - 1.5 * i, 3.6, 0.9, "list [0, 0, 0]", fc="#e3f6e3", ec="#2e7d32")
        arrow(ax, (3.8, 4.65 - 1.5 * i), (6.0, 4.65 - 1.5 * i))
    ax.text(5, 0.3, "three separate row objects:\ngood[0] is good[1] -> False", ha="center", fontsize=8)
    save(fig, "q2_memory.png")

    # ---------------- Q3
    r = load("Q3")
    line_plot(r["timing"], "n", [("dict_get", "dict + get()"), ("counter", "Counter"),
                                 ("list_count", "list.count() per word")],
              "Q3: word counting (log-log)", "q3_timing.png", xlabel="number of complaints")

    # ---------------- Q4 Venn diagrams
    xs, ys = np.meshgrid(np.linspace(0, 10, 500), np.linspace(0, 6, 300))
    inA = (xs - 3.9) ** 2 + (ys - 3) ** 2 <= 1.9 ** 2
    inB = (xs - 6.1) ** 2 + (ys - 3) ** 2 <= 1.9 ** 2
    regions = [("A & B  (clash)", inA & inB), ("A - B  (only AI)", inA & ~inB), ("B - A  (only IoT)", inB & ~inA),
               ("A ^ B  (exactly one)", inA ^ inB), ("A | B  (either)", inA | inB),
               ("U - (A | B)  (neither)", ~(inA | inB))]
    fig, axes = plt.subplots(2, 3, figsize=(9, 5.2))
    for ax, (title, mask) in zip(axes.ravel(), regions):
        ax.imshow(mask, extent=(0, 10, 0, 6), origin="lower", cmap="Blues", vmin=0, vmax=1.6, alpha=0.9)
        for cx, lab in ((3.9, "A"), (6.1, "B")):
            ax.add_patch(plt.Circle((cx, 3), 1.9, fill=False, ec="k", lw=1.2))
            ax.text(cx + (-1.9 if lab == "A" else 1.9) * 0.55, 5.3, lab, ha="center", fontsize=10, weight="bold")
        ax.add_patch(Rectangle((0.02, 0.02), 9.96, 5.96, fill=False, ec="k", lw=1))
        ax.text(0.3, 0.3, "U", fontsize=9)
        ax.set_title(title, fontsize=9); ax.axis("off")
    save(fig, "q4_venn.png")

    r = load("Q4")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
    ax = axes[0]
    ax.plot([d["n"] for d in r["membership"]], [d["list"] for d in r["membership"]], "o-", label="x in list")
    ax.plot([d["n"] for d in r["membership"]], [d["set"] for d in r["membership"]], "o-", label="x in set")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title("membership test (worst case)", fontsize=10)
    ax.set_xlabel("n"); ax.set_ylabel("seconds per lookup"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    ax = axes[1]
    for key, label in (("nested", "nested loops"), ("sorted", "sort + walk"), ("set", "set &")):
        ax.plot([d["n"] for d in r["common"]], [d[key] for d in r["common"]], "o-", label=label)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title("finding common students", fontsize=10)
    ax.set_xlabel("n (size of each list)"); ax.set_ylabel("seconds"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    save(fig, "q4_timing.png")

    # ---------------- Q5
    r = load("Q5")
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    width = 0.25
    for i, (key, label) in enumerate((("loop", "for + append"), ("comp", "list comprehensions"),
                                      ("mapfilter", "map / filter"))):
        ax.bar(np.arange(3) + (i - 1) * width, [d[key] for d in r["timing"]], width, label=label)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{d['n']:,}" for d in r["timing"]])
    ax.set_yscale("log"); ax.set_xlabel("readings"); ax.set_ylabel("time (s)")
    ax.set_title("Q5: cleaning + conversion + alarms", fontsize=10); ax.legend(fontsize=8); ax.grid(True, axis="y", alpha=0.3)
    save(fig, "q5_timing.png")

    # ---------------- Q6 nested structure + timing
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")
    box(ax, 0.1, 2.5, 2.0, 1.0, "timetable\n(dict)\ntrain_no -> info", fc="#fff3cd", ec="#a07800")
    box(ax, 3.0, 2.5, 2.0, 1.0, "12001\n(dict)\n{name, stops, days}", fc="#e8f1fb")
    arrow(ax, (2.1, 3.0), (3.0, 3.0))
    box(ax, 6.2, 4.4, 2.4, 0.9, "'name' -> str")
    box(ax, 6.2, 2.6, 2.4, 0.9, "'stops' -> list\n(ordered stops)", fc="#e3f6e3", ec="#2e7d32")
    box(ax, 6.2, 0.7, 2.4, 0.9, "'days' -> set\n{'Mon','Wed',...}", fc="#fde2e2", ec="#b00020")
    for yy in (4.85, 3.05, 1.15):
        arrow(ax, (5.0, 3.0), (6.2, yy))
    for k in range(3):
        box(ax, 9.3, 4.0 - 1.1 * k + 0.0, 2.5, 0.8,
            ("('Chennai Central','--','06:00')", "('Villupuram','08:10','08:12')", "('Tiruchirappalli','10:30','10:35')")[k],
            fc="#f3e8fd", ec="#6a1b9a", fs=6.5)
        arrow(ax, (8.6, 3.05), (9.3, 4.4 - 1.1 * k))
    ax.text(10.55, 0.9, "tuple (station, arrival, departure)\n[2][2] -> departure of 3rd station",
            ha="center", fontsize=7.5)
    ax.text(0.1, 0.2, "timetable[12001]['stops'][2][2]  ->  '10:35'", fontsize=9, family="monospace")
    save(fig, "q6_nested.png")

    r = load("Q6")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
    ax = axes[0]
    for key, label in (("scan", "nested scan"), ("flat", "flat list scan"), ("indexed", "station index")):
        ax.plot([d["trains"] for d in r["timing"]], [d[key] for d in r["timing"]], "o-", label=label)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("trains"); ax.set_ylabel("seconds per query")
    ax.set_title("station query time", fontsize=10); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    ax = axes[1]
    ax.bar([str(d["trains"]) for d in r["timing"]], [d["index_bytes"] / 1024 for d in r["timing"]], color="#6a1b9a")
    ax.set_xlabel("trains"); ax.set_ylabel("extra memory (KiB)"); ax.set_title("memory used by the index", fontsize=10)
    save(fig, "q6_timing.png")

    # ---------------- Q7
    r = load("Q7")
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ax.plot([d["n"] for d in r["pair_timing"]], [d["pairwise"] for d in r["pair_timing"]], "o-", label="compare every pair")
    ax.plot([d["n"] for d in r["pair_timing"]], [d["dict"] for d in r["pair_timing"]], "o-", label="dictionary")
    ax.plot([d["n"] for d in r["dict_timing"]], [d["dict"] for d in r["dict_timing"]], "s--", label="dictionary (1k, 100k)")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("contacts n"); ax.set_ylabel("seconds")
    ax.set_title("Q7: merging contacts (log-log)", fontsize=10); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    save(fig, "q7_timing.png")


if __name__ == "__main__":
    make_all()
    print("Figures saved in", FIG)
