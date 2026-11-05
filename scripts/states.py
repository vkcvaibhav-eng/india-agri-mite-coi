"""Shared matching of Indian state and territory names, tolerant of OCR damage.

Used by every checklist parser so that all sources report states under the same
spelling. Names are kept as the sources print them: the 1985 book has no
Jharkhand, Chhattisgarh, Uttarakhand or Telangana, newer lists do, and a state
that was split since is not re-assigned here.
"""
import difflib
import re

# States and territories as the book names them (1985 boundaries). Each key is a
# spelling or OCR-damaged form already seen; everything else is matched fuzzily.
STATES = {
    "Andhra Pradesh": ["andhrapradesh", "ap"],
    "Arunachal Pradesh": ["arunachalpradesh", "nefa"],
    "Assam": ["assam"],
    "Bihar": ["bihar"],
    "Delhi": ["delhi", "newdelhi"],
    "Goa": ["goa"],
    "Gujarat": ["gujarat"],
    "Haryana": ["haryana"],
    "Himachal Pradesh": ["himachalpradesh", "hp"],
    "Jammu & Kashmir": ["jammukashmir", "jammu", "kashmir", "jk"],
    "Karnataka": ["karnataka", "kamataka", "mysore"],
    "Kerala": ["kerala"],
    "Madhya Pradesh": ["madhyapradesh", "mp"],
    "Maharashtra": ["maharashtra"],
    "Manipur": ["manipur"],
    "Meghalaya": ["meghalaya"],
    "Mizoram": ["mizoram"],
    "Nagaland": ["nagaland"],
    "Orissa": ["orissa", "odisha"],
    "Chhattisgarh": ["chhattisgarh", "chattisgarh"],
    "Jharkhand": ["jharkhand"],
    "Uttarakhand": ["uttarakhand", "uttaranchal"],
    "Telangana": ["telangana"],
    "Ladakh": ["ladakh"],
    "Punjab": ["punjab"],
    "Rajasthan": ["rajasthan"],
    "Sikkim": ["sikkim"],
    "Tamil Nadu": ["tamilnadu", "madras"],
    "Tripura": ["tripura"],
    "Uttar Pradesh": ["uttarpradesh", "up"],
    "West Bengal": ["westbengal", "wbengal", "bengal"],
    "Andaman & Nicobar Islands": ["andaman", "nicobar", "carnicobar", "andamannicobar"],
    "Pondicherry": ["pondicherry", "pondichery"],
    "Chandigarh": ["chandigarh"],
    "Lakshadweep": ["lakshadweep", "laccadive"],
}
STATE_KEYS = {alias: name for name, aliases in STATES.items() for alias in aliases}


def state_of(token):
    """One state name from a piece of OCR text, or '' if it does not look like one."""
    t = re.sub(r"[^a-z]", "", token.lower().replace("&", ""))
    if len(t) > 6 and t.endswith(("isis", "islands", "island", "isi", "isl", "is")) and not t.endswith(("assam",)):
        stripped = re.sub(r"(isis|islands?|isi|isl|is)$", "", t)
        t = stripped if len(stripped) >= 5 else t
    if t.startswith(("nicob", "andam", "carnic")):
        return "Andaman & Nicobar Islands"
    if t in STATE_KEYS:
        return STATE_KEYS[t]
    if len(t) < 4:
        return ""
    hit = difflib.get_close_matches(t, [k for k in STATE_KEYS if len(k) > 3], n=1, cutoff=0.74 if len(t) >= 8 else 0.82)
    return STATE_KEYS[hit[0]] if hit else ""




def clean_states(text):
    """Split an INDIA: list into canonical states; return (states, unmatched pieces)."""
    states, unmatched = [], []
    text = re.sub(r"\s+", " ", text).strip(" .;")
    for short, full in ((r"\bU\s*\.?\s*[Pp]\b\.?", "Uttar Pradesh"), (r"\bM\s*\.?\s*P\b\.?", "Madhya Pradesh"),
                        (r"\bH\s*\.?\s*[Pp]\b\.?", "Himachal Pradesh"), (r"\bA\s*\.?\s*P\b\.?", "Andhra Pradesh"),
                        (r"\bJ\s*\.?\s*&\.?\s*K\b\.?", "Jammu & Kashmir"), (r"\bW\s*\.\s*Bengal", "West Bengal"),
                        (r"Jammu\s*&\.?\s*Kashmir", "Jammu & Kashmir")):
        text = re.sub(short, full, text)
    for part in re.split(r"[,;]|\sand\s|\.\s", text):
        piece = part.strip(" .:()'\"?-_")
        if not piece:
            continue
        name = state_of(piece)
        if name:
            if name not in states:
                states.append(name)
        elif len(piece) > 2:
            unmatched.append(piece)
    return states, unmatched
