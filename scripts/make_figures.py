"""Paper 1 results: tables (CSV) and figures (PNG 300 dpi and TIFF).

Table 1  COI coverage of the Indian checklist, by group
Table 2  best-close-match outcome of named Indian COI sequences, by group
Table 3  sequences whose name disagrees with their ASAP group (from suspect_names.csv)
Figure 1 COI coverage by group (share of species with Indian COI, COI only from abroad, none)
Figure 2 best-close-match outcome of named Indian COI sequences, by group
"""
import csv
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
PR = os.path.join(ROOT, "data", "processed")
OUT_T = os.path.join(ROOT, "results", "tables")
OUT_F = os.path.join(ROOT, "results", "figures")
os.makedirs(OUT_T, exist_ok=True)
os.makedirs(OUT_F, exist_ok=True)
GROUPS = ["Tetranychidae", "Tenuipalpidae", "Eriophyoidea", "Tarsonemidae", "Tuckerellidae", "Phytoseiidae"]
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK})


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name, data):
    with open(os.path.join(OUT_T, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)


# ---- Table 1 / Figure 1 -------------------------------------------------------------
cov = rows(os.path.join(PR, "coverage_by_species.csv"))
t1 = []
for g in GROUPS + ["All groups"]:
    cs = [c for c in cov if g == "All groups" or c["group"] == g]
    n = len(cs)
    anyc = sum(int(c["n_coi"]) > 0 for c in cs)
    ind = sum(int(c["n_coi_india"]) > 0 for c in cs)
    t1.append({"Group": g, "Species in checklist": n,
               "Species with COI (any country)": anyc, "% with COI": f"{100 * anyc / n:.1f}",
               "Species with COI from India": ind, "% with Indian COI": f"{100 * ind / n:.1f}",
               "COI records (unique)": sum(int(c["n_coi"]) for c in cs),
               "Indian COI records": sum(int(c["n_coi_india"]) for c in cs)})
write("table1_coi_coverage.csv", t1)

fig, ax = plt.subplots(figsize=(6.8, 2.9), dpi=300)
DARK, LIGHT, NONE = "#256abf", "#86b6ef", "#ecebe7"
labels = []
for i, g in enumerate(GROUPS[::-1]):
    r = next(x for x in t1 if x["Group"] == g)
    n = r["Species in checklist"]
    ind, abroad = r["Species with COI from India"], r["Species with COI (any country)"] - r["Species with COI from India"]
    a, b = 100 * ind / n, 100 * abroad / n
    ax.barh(i, a, color=DARK, height=0.62, edgecolor=SURFACE, linewidth=1)
    ax.barh(i, b, left=a, color=LIGHT, height=0.62, edgecolor=SURFACE, linewidth=1)
    ax.barh(i, 100 - a - b, left=a + b, color=NONE, height=0.62, edgecolor=SURFACE, linewidth=1)
    ax.text(101.5, i, f"{ind + abroad} of {n} with COI", va="center", ha="left",
            fontsize=8, color=INK2)
    labels.append(f"{g} (n = {n})")
ax.set_yticks(range(len(GROUPS)))
ax.set_yticklabels(labels)
ax.set_xlim(0, 100)
ax.set_xlabel("Species in the Indian checklist (%)")
ax.xaxis.grid(True, color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color=DARK, label="COI sequence from India"),
                   Patch(color=LIGHT, label="COI sequence only from other countries"),
                   Patch(color=NONE, label="No COI sequence")],
          loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("png", "tiff"):
    fig.savefig(os.path.join(OUT_F, f"fig1_coi_coverage.{ext}"), dpi=300, facecolor=SURFACE,
                **({"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tiff" else {}))
plt.close(fig)

# ---- Table 2 / Figure 2 -------------------------------------------------------------
cl = [x for x in rows(os.path.join(PR, "delimitation", "clusters.csv"))
      if x["india_record"] == "1" and x["match_basis"] not in ("no_species_name", "cf_or_aff")]
CATS = [("correct", "Correct"), ("ambiguous", "Ambiguous"), ("incorrect", "Incorrect"),
        ("no match within 3%", "No match within 3%")]
by = defaultdict(Counter)
names = defaultdict(set)
for x in cl:
    by[x["group"]][x["best_close_match"]] += 1
    names[x["group"]].add(x["name"])
t2 = []
for g in [g for g in GROUPS if by[g]] + ["All groups"]:
    c = Counter() if g != "All groups" else sum(by.values(), Counter())
    if g != "All groups":
        c = by[g]
    n = sum(c[k] for k, _ in CATS) + c["no overlapping sequence"]
    row = {"Group": g, "Named Indian sequences": n,
           "Names": len(names[g]) if g != "All groups" else len(set().union(*names.values()))}
    for k, lab in CATS:
        v = c[k] + (c["no overlapping sequence"] if k == "no match within 3%" else 0)
        row[lab] = v
        row[f"% {lab.lower()}"] = f"{100 * v / n:.1f}"
    t2.append(row)
write("table2_best_close_match.csv", t2)

fig, ax = plt.subplots(figsize=(6.8, 2.5), dpi=300)
COL = {"Correct": "#2a78d6", "Ambiguous": "#eda100", "Incorrect": "#e34948", "No match within 3%": "#b9b8b3"}
gs = [r for r in t2 if r["Group"] != "All groups"][::-1]
for i, r in enumerate(gs):
    left = 0
    for _, lab in CATS:
        v = 100 * r[lab] / r["Named Indian sequences"]
        ax.barh(i, v, left=left, color=COL[lab], height=0.62, edgecolor=SURFACE, linewidth=1)
        if v >= 3.5:
            ax.text(left + v / 2, i, f"{r[lab]}", ha="center", va="center", fontsize=7,
                    color="#ffffff" if lab in ("Correct", "Incorrect") else INK)
        left += v
    ax.text(101.5, i, f"n = {r['Named Indian sequences']}", va="center", fontsize=8, color=INK2)
ax.set_yticks(range(len(gs)))
ax.set_yticklabels([r["Group"] for r in gs])
ax.set_xlim(0, 100)
ax.set_xlabel("Named Indian COI sequences (%)")
ax.xaxis.grid(True, color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.legend(handles=[Patch(color=COL[lab], label=lab) for _, lab in CATS], loc="lower center",
          bbox_to_anchor=(0.45, 1.0), ncol=4, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("png", "tiff"):
    fig.savefig(os.path.join(OUT_F, f"fig2_best_close_match.{ext}"), dpi=300, facecolor=SURFACE,
                **({"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tiff" else {}))
plt.close(fig)

# ---- Table 3 ------------------------------------------------------------------------
sus = rows(os.path.join(PR, "suspect_names.csv"))
seen, t3 = set(), []
for s in sus:
    k = s["accession"]
    if k in seen:
        continue
    seen.add(k)
    t3.append({"Accession": s["accession"], "Name on record": s["name_on_record"],
               "ASAP group (majority name)": s["group_majority_name"], "Indian record": s["indian"],
               "Country": s["country"], "Host": s["host"], "COI region (reference sites)": s["region"].split("_")[-1],
               "ASAP partition": s["asap_partition"]})
t3.sort(key=lambda r: (r["ASAP group (majority name)"], r["Indian record"] != "yes", r["Accession"]))
write("table3_names_in_conflict_with_asap.csv", t3)
print("tables:", os.listdir(OUT_T))
print("figures:", os.listdir(OUT_F))
