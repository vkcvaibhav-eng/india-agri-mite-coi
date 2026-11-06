"""Name parsing shared by the checklist scripts."""
import re

# Genus, optional (Subgenus), epithet. The genus must be followed by a space, so an
# OCR-damaged name such as "Typhlodromus (Ty phloctomus) nesbitti" fails instead of
# being read as "Typhlodro mus".
NAME = re.compile(r"\s*([A-Z][a-z]+)(?:\s+\(\s*([A-Z][a-z]+)\s*\))?\s+([a-z][a-z-]{2,})(?![A-Za-z])")
NOT_EPITHET = {"sp", "spp", "nr", "cf", "near", "nov", "and", "et", "var", "group", "sensu", "species"}
NOT_GENUS = {"This", "These", "The", "That", "Female", "Male", "Host", "Hosts", "See", "Also", "From", "With"}
AUTH_YEAR = re.compile(r"\s*\(?\s*([A-Z][^,()0-9;:]{1,60}?)\s*,?\s*(1[789]\d\d|20[0-2]\d)\b")


def parse(s):
    """(genus, subgenus or '', epithet) from the start of a printed name, or None."""
    m = NAME.match((s or "").replace("/", "l"))
    if not m or m.group(3) in NOT_EPITHET or m.group(1) in NOT_GENUS or len(m.group(1)) < 4:
        return None
    return m.group(1), m.group(2) or "", m.group(3)


def display(g, sg, e):
    return f"{g} ({sg}) {e}" if sg else f"{g} {e}"


def key(g, e):
    return f"{g.lower()} {e.lower()}"


def parse_cited(text):
    """(name, author, year) from the start of a taxonomic citation.

    'Tenuipalpus phoenicis Geijskes, 1939, ...' gives the authority and year of the
    name. 'Brevipalpus phoenicis, Ghai & Shenhmer, 1984' is a later use of the name
    by those authors, so author and year are left empty."""
    t = (text or "").replace("/", "l")
    m = NAME.match(t)
    if not m or m.group(3) in NOT_EPITHET or m.group(1) in NOT_GENUS or len(m.group(1)) < 4:
        return None, "", ""
    name = (m.group(1), m.group(2) or "", m.group(3))
    rest = t[m.end():]
    if re.match(r"\s*[,;:]", rest):
        return name, "", ""
    a = AUTH_YEAR.match(rest)
    return (name, a.group(1).strip(), a.group(2)) if a else (name, "", "")


def first_author(a):
    """Surname of the first author, lower case, letters only."""
    a = re.sub(r"[()\[\]]", " ", a or "")
    a = re.split(r"\b(?:1[789]\d\d|20\d\d)\b", a)[0]
    a = re.split(r"\s*(?:&|,|\band\b|\bet\.?\s*al\b)\s*", a.strip())[0]
    return re.sub(r"[^a-z]", "", a.lower())


def stem(e):
    """Epithet without its Latin ending, so that indicus and indica compare equal."""
    return re.sub(r"(iae|ii|ae|us|um|is|a|e|i)$", "", e)
