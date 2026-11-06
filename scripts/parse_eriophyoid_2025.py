"""Species lists of two 2025 eriophyoid papers: Som et al. 2025 (Uttar Pradesh Journal of Zoology; South Bengal,
numbered Table 1) and Dyamanagouda et al. 2025/2026 (Indian Journal of Entomology 88(1); Karnataka Table 1)."""
import re, csv, sys
D = "/home/claude/src/erio/"
def clean(g, e): return f"{g} {e}"
# Som et al. 2025
som = []
for l in open(D + "som2025.txt", errors="replace"):
    m = re.match(r"^(\d{1,2})\.\s+([A-Z][a-z]+)\s+([a-z][a-z-]+)\b(.*)$", l)
    if m and int(m.group(1)) <= 60:
        som.append((int(m.group(1)), clean(m.group(2), m.group(3)), re.sub(r"\s{2,}.*", "", m.group(4)).strip()))
src = open(D + "som2025.txt", errors="replace").read().split("\n")
for i, l in enumerate(src):
    m = re.match(r"^(\d{1,2})\.\s+([A-Z][a-z]{4,})\s{2,}", l)
    if m and int(m.group(1)) <= 60:
        nxt = re.match(r"^\s+([a-z][a-z-]+)\b", src[i + 1]) if i + 1 < len(src) else None
        if nxt: som.append((int(m.group(1)), f"{m.group(2)} {nxt.group(1)}", ""))
seen = {}
for n, sp, au in som: seen.setdefault(n, (sp, au))
with open("data/checklist/som2025_eriophyoidea_south_bengal.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["number", "species", "authority_fragment", "india_states"])
    for n in sorted(seen): w.writerow([n, seen[n][0], seen[n][1], "West Bengal"])
print("Som 2025:", len(seen), "of 60 expected; missing", [i for i in range(1, 61) if i not in seen])
# Karnataka
lines = open(D + "karn2025.txt", errors="replace").read().split("\n")
a = next(i for i, l in enumerate(lines) if "Table 1. Eriophyoid mites fauna" in l)
b = min(len(lines), a + 135)
out = []
for l in lines[a:b]:
    m = re.match(r"^(?:[A-Za-z, ]{0,28})\s{3,}([A-Z][a-z]+)\s+([a-z][a-z-]+)\b(.*)$", l) or re.match(r"^\s{20,}([A-Z][a-z]+)\s+([a-z][a-z-]+)\b(.*)$", l)
    if m and m.group(1) not in ("Table", "Eriophyoid", "Host", "Mite", "Remarks", "Roy", "Chakrabarti", "Moraes", "Bauhinia", "Millingtonia"):
        new = "New record to" in l
        out.append((clean(m.group(1), m.group(2)), 1 if new else 0))
names = []
for n, new in out:
    if n not in [x[0] for x in names]: names.append((n, new))
with open("data/checklist/dyamanagouda2025_eriophyoidea_karnataka.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["species", "new_record_india", "india_states"])
    for n, new in names: w.writerow([n, new, "Karnataka"])
print("Karnataka 2025:", len(names), "new India records:", sum(x[1] for x in names))
