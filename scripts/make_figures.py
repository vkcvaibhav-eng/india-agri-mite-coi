"""Paper 1 results: tables (CSV) and figures (PNG 300 dpi and TIFF).

table1_coi_coverage.csv                 Table 1  COI coverage of the Indian checklist, by group
table2_name_agreement_sensitivity.csv   Table 2  same-name agreement by comparator pool and threshold
table3_names.csv                        Table 3  per name borne by Indian sequences: agreement and ASAP groups
table4_asap_abgd_partitions.csv         Table 4  ASAP and ABGD partitions of the 15 files analysed
table5_names_in_conflict_with_asap.csv  Table 5  ASAP groups holding more than one name
table_best_close_match_by_group.csv     counts behind Figure 1
fig1_name_agreement.{png,tiff}          Figure 1 nearest-neighbour name agreement by group (all comparators, 3%)
fig_coi_coverage.{png,tiff}             coverage by group (not in the manuscript; Table 1 holds the numbers)
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
OUTSIDE = Counter(m["species_id"] for m in rows(os.path.join(PR, "coi_matched.csv"))
                  if m["species_id"] and m["is_representative"] == "1" and m["geo_status"] == "outside")
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
               "Indian COI records": sum(int(c["n_coi_india"]) for c in cs),
               "Species with Indian COI and none documented from outside India":
                   sum(int(c["n_coi_india"]) > 0 and OUTSIDE[c["species_id"]] == 0 for c in cs)})
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
    fig.savefig(os.path.join(OUT_F, f"fig_coi_coverage.{ext}"), dpi=300, facecolor=SURFACE,
                **({"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tiff" else {}))
plt.close(fig)

# ---- Table 2 / Figure 2 -------------------------------------------------------------
cl = [x for x in rows(os.path.join(PR, "delimitation", "clusters.csv"))
      if x["india_record"] == "1" and x["match_basis"] not in ("no_species_name", "cf_or_aff")]
CATS = [("same name", "Same-name match"), ("ambiguous", "Ambiguous"), ("different name", "Different-name match"),
        ("no match", "No match within 3%")]
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
    n = sum(c[k] for k, _ in CATS) + c["no comparator"]
    row = {"Group": g, "Named Indian sequences": n,
           "Names": len(names[g]) if g != "All groups" else len(set().union(*names.values()))}
    for k, lab in CATS:
        v = c[k] + (c["no comparator"] if k == "no match" else 0)
        row[lab] = v
        row[f"% {lab.lower()}"] = f"{100 * v / n:.1f}"
    t2.append(row)
write("table_best_close_match_by_group.csv", t2)

# Figure 1: 13 cm wide (one Acarologia column), 600 dpi, colour online with hatching so that
# the four classes stay distinct in the black-and-white print edition
plt.rcParams.update({"font.size": 7, "hatch.linewidth": 0.6})
fig, ax = plt.subplots(figsize=(13 / 2.54, 5.2 / 2.54))
COL = {"Same-name match": "#2a78d6", "Ambiguous": "#eda100", "Different-name match": "#e34948",
       "No match within 3%": "#d9d8d4"}
HATCH = {"Same-name match": "", "Ambiguous": "////", "Different-name match": "xxxx", "No match within 3%": "...."}
gs = [r for r in t2 if r["Group"] != "All groups"][::-1]
for i, r in enumerate(gs):
    left = 0
    for _, lab in CATS:
        v = 100 * r[lab] / r["Named Indian sequences"]
        ax.barh(i, v, left=left, color=COL[lab], height=0.62, edgecolor="#000000", linewidth=0.4,
                hatch=HATCH[lab])
        if v >= 4:
            ax.text(left + v / 2, i, f"{r[lab]}", ha="center", va="center", fontsize=6.5,
                    color="#ffffff" if lab == "Same-name match" else INK,
                    bbox=None if lab == "Same-name match" else dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
        left += v
    ax.text(101.5, i, f"n = {r['Named Indian sequences']}", va="center", fontsize=6.5, color=INK)
ax.set_yticks(range(len(gs)))
ax.set_yticklabels([r["Group"] for r in gs])
ax.set_xlim(0, 100)
ax.set_xlabel("Named Indian COI sequences (%)")
ax.xaxis.grid(True, color=GRID, linewidth=0.5)
ax.set_axisbelow(True)
for s_ in ("top", "right", "left"):
    ax.spines[s_].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.legend(handles=[Patch(facecolor=COL[lab], edgecolor="#000000", linewidth=0.4, hatch=HATCH[lab], label=lab)
                   for _, lab in CATS], loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=4, frameon=False,
          fontsize=6.5, handlelength=1.6, columnspacing=1.0)
fig.tight_layout(pad=0.3)
fig.savefig(os.path.join(OUT_F, "fig1_name_agreement.tiff"), dpi=600, facecolor=SURFACE,
            pil_kwargs={"compression": "tiff_lzw"})
fig.savefig(os.path.join(OUT_F, "fig1_name_agreement.png"), dpi=600, facecolor=SURFACE)
fig.savefig(os.path.join(OUT_F, "fig1_name_agreement.svg"), facecolor=SURFACE)
plt.close(fig)
plt.rcParams.update({"font.size": 9})

# ---- Table 2: sensitivity -----------------------------------------------------------
POOLS = [("all", "All comparators"), ("holdout", "Comparators from other institutions"),
         ("outside", "Comparators documented from outside India")]
t2s = []
for pool, plab in POOLS:
    for t in (1, 2, 3, 4, 5):
        c = Counter(x[f"bcm_{pool}_{t}"] for x in cl)
        per = defaultdict(list)
        for x in cl:
            per[x["name"]].append(x[f"bcm_{pool}_{t}"] == "same name")
        t2s.append({"Comparator pool": plab, "Threshold (%)": t, "Same-name match": c["same name"],
                    "Ambiguous": c["ambiguous"], "Different-name match": c["different name"],
                    "No match": c["no match"] + c["no comparator"],
                    "% same-name (sequences)": f"{100 * c['same name'] / len(cl):.1f}",
                    "% same-name (names weighted equally)": f"{100 * sum(sum(v) / len(v) for v in per.values()) / len(per):.1f}"})
write("table2_name_agreement_sensitivity.csv", t2s)

# ---- ASAP partitions used --------------------------------------------------------------
import glob  # noqa: E402
import re  # noqa: E402
HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, "read_asap.py")).read().split("rows, summ = [], []")[0])
HAVE_ASAP = os.path.isdir(RES) and bool(os.listdir(RES))
RUNS = {os.path.basename(r): asap_groups(os.path.basename(r)) for r in sorted(glob.glob(os.path.join(RES, "*")))} \
    if HAVE_ASAP else {}
UNNAMED = re.compile(r"\b(sp|cf|aff)\b")
asap_of = defaultdict(list)    # name -> [(region, n groups, other names)]
t4 = []
for run, target in RUNS.items():
    labels, nsub, assign, dist = read_spart(glob.glob(os.path.join(RES, run, "asap", "*.fas.spart"))[0])
    idx = asap_index(labels, nsub, asap_row(run))
    subs = defaultdict(list)
    for smp, v in assign.items():
        subs[v[idx]].append(name_of(smp)[0])
    by_name = defaultdict(set)
    for k, ns in subs.items():
        for n in ns:
            by_name[n].add(k)
    for n, ks in by_name.items():
        if UNNAMED.search(n):
            continue
        others = sorted({o for k in ks for o in subs[k] if o != n and not UNNAMED.search(o)})
        asap_of[n].append((run.split("_")[-1].replace("sites", ""), len(ks), others))
    ind = sum(name_of(smp)[1] for smp in assign)
    summ_ = [r for r in rows(os.path.join(ROOT, "logs", "delimitation_summary.csv")) if r["run"] == run]
    abgd = next((r for r in summ_ if r["method"] == "ABGD"), {})
    asap1 = next((r for r in summ_ if r["method"] == "ASAP"), {})
    def label(r):
        g, s = r.split("_sites")
        return f"{g} ({s.replace('-', '–')})"
    t4.append({"File (reference sites)": label(run), "Sequences": len(assign), "Indian sequences": ind,
               "Names": len({n for ns in subs.values() for n in ns if not UNNAMED.search(n)}),
               "ASAP groups": target,
               "ASAP threshold (%)": f"{100 * float(asap1.get('threshold') or 0):.1f}",
               "ABGD groups at P = 0.0129": ("none" if not abgd or "no usable" in abgd.get("threshold", "")
                                             else abgd["subsets"])})
if t4:
    write("table4_asap_abgd_partitions.csv", t4)

# ---- Table 3: per name -----------------------------------------------------------------
t3 = []
for (g, n) in sorted({(x["group"], x["name"]) for x in cl}, key=lambda k: (GROUPS.index(k[0]), k[1])):
    xs = [x for x in cl if x["name"] == n and x["group"] == g]
    c = Counter(x["bcm_all_3"] for x in xs)
    co = Counter(x["bcm_outside_3"] for x in xs)
    ov = [float(x["min_dist_foreign_same_name"]) for x in xs if x["min_dist_foreign_same_name"]]
    a = asap_of.get(n, [])
    t3.append({"Group": g, "Name on Indian records": n, "Indian sequences": len(xs),
               "With a same-name record documented outside India": len(ov),
               "Least distance to that record (%)": f"{100 * min(ov):.1f}" if ov else "–",
               "Same-name match": c["same name"], "Ambiguous": c["ambiguous"],
               "Different-name match": c["different name"], "No match": c["no match"] + c["no comparator"],
               "Same-name match, outside-India comparators only": co["same name"],
               "ASAP groups (other names sharing them)": "; ".join(
                   f"sites {r}: {k} group{'s' if k > 1 else ''}" + (f" with {', '.join(o)}" if o else "")
                   for r, k, o in a) or "–"})
write("table3_names.csv", t3)

# ---- Table 5: ASAP groups that hold more than one name -----------------------------------
sus = rows(os.path.join(PR, "suspect_names.csv")) if HAVE_ASAP else []
ORIGIN = {"india": "India", "unknown": "origin not given"}
HOST = {"okra": "okra", "mulberry": "mulberry", "lab culture-mulberry": "mulberry culture", "vitis vinifera": "grape",
        "musa sp.": "banana", "oryza sativa (rice)": "rice", "rice": "rice", "sorghum": "sorghum", "bamboo": "bamboo",
        "asparagus sp.": "asparagus", "citrus sp.": "citrus", "carnation": "carnation", "cucumber": "cucumber",
        "solanum lycopersicum": "tomato", "tomato": "tomato", "ixora chinensis": "Ixora chinensis"}
by_group = defaultdict(list)
for s_ in sus:
    by_group[(s_["region"], s_["asap_group"])].append(s_)


def short(name, genus_seen):
    g, rest = name.split(" ", 1)
    if g in genus_seen:
        return f"{g[0]}. {rest}"
    genus_seen.add(g)
    return name


t5 = []
for (region, grp), ss in by_group.items():
    seen_g = set()
    comp = "; ".join(f"{short(c.rsplit(' ', 1)[0], seen_g)} {c.rsplit(' ', 1)[1]}"
                     for c in ss[0]["group_composition"].split("; "))
    tie = ss[0]["conflict"] == "tie"
    parts = defaultdict(list)
    for s_ in ss:
        o = ORIGIN.get(s_["geo_status"], s_["country"])
        h = HOST.get(s_["host"].strip().lower(), s_["host"].strip())
        parts[s_["name_on_record"]].append(f"{s_['accession'].split('.')[0]} ({o}{', ' + h if h and s_['geo_status'] == 'india' else ''})")
    seen_g = set()
    detail = "; ".join(f"{short(n, seen_g)}: {', '.join(v)}" for n, v in parts.items())
    g, sites = region.split("_sites")
    t5.append({"File (reference sites)": f"{g} ({sites.replace('-', '–')})",
               "Names in the ASAP group (sequences)": comp,
               "Majority name": "tie" if tie else ss[0]["group_majority_name"],
               "Sequences in conflict": detail,
               "Indian sequences in conflict": sum(s_["geo_status"] == "india" for s_ in ss)})
ORDER = ["Tetranychus", "Oligonychus", "Schizotetranychus", "Aceria", "Phytoseiidae"]
t5.sort(key=lambda r: (ORDER.index(r["File (reference sites)"].split(" ")[0]) if r["File (reference sites)"].split(" ")[0] in ORDER else 9,
                       r["File (reference sites)"], -r["Indian sequences in conflict"], r["Names in the ASAP group (sequences)"]))
if t5:
    write("table5_names_in_conflict_with_asap.csv", t5)
print("tables:", sorted(os.listdir(OUT_T)))
print("figures:", sorted(os.listdir(OUT_F)))
