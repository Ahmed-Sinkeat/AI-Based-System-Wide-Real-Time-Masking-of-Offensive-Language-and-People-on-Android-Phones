"""Combine every Arabic bad-word list we found into one file: ar_combined.tsv

    python3 build_ar.py          # rebuild ar_combined.tsv from sources/
    python3 build_ar.py --test   # self-check of the normalizer and parsers

One row per normalized term. The `sources` column says where each term came from, so a source can be dropped
later (for example Attia's, if he does not give permission). See README.md for sources and licenses.
"""
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "sources"

# Attia's section numbers -> our four categories (swearing / sexual / insult / blasphemy). The team reviews these.
ATTIA_TO_OURS = {"1": "sexual", "2": "swearing", "3": "swearing", "4": "insult", "5": "insult",
                 "6": "insult", "7": "insult", "8": "swearing"}

TASHKEEL = re.compile("[ً-ْٰـ]")  # harakat, shadda, sukun, superscript alef, tatweel
AR_LETTER = re.compile("[ء-ي]")


def normalize(s):
    """Same rules as Lucene's ArabicNormalizer, plus trim/lowercase, and hashtag/joiner signs -> space
    (screen text is split into words, so '#افلام_سكس' must become the phrase 'افلام سكس'). De-duplication key."""
    s = re.sub(r"[#_.\-]+", " ", s.replace("﻿", "")).strip().lower()
    s = TASHKEEL.sub("", s)
    s = re.sub("[أإآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", s)


def lines(name):
    return [l for l in (SRC / name).read_text(encoding="utf-8-sig").splitlines() if l.strip()]


def parse_attia(text):
    """'* **term / term (translit):** note' under '### N. Title' (and '#### A. Title') headings -> (term, section, title)."""
    out, sec, title = [], None, None
    for l in text.split("# Offensive Word Categories", 1)[1].splitlines():
        if m := re.match(r"###\s+(\d+)\.\s*(.+)", l):
            sec, title = m.group(1), m.group(2).strip()
        elif m := re.match(r"####\s+\w\.\s*(.+)", l):
            title = m.group(1).strip()
        elif m := re.match(r"\*\s+\*\*(.+?)\*\*", l):
            terms = m.group(1).rsplit(" (", 1)[0]                          # drop the transliteration (last bracket)
            out += [(re.sub(r"[()]", "", t).strip(" :"), sec, title) for t in terms.split("/") if AR_LETTER.search(t)]
    return out


def parse_cuss(text):
    """ar-latn.js: `'word': rating,` lines -> (word, rating)."""
    return re.findall(r"""^\s*['"]?([^'":]+?)['"]?\s*:\s*(\d)""", text, re.M)


def build():
    rows = {}  # key -> row

    def add(term, source, attia_cat="", ours="", note=""):
        key = normalize(term)
        if not key:
            return
        r = rows.setdefault(key, dict(key=key, term=term.strip(), script="arabic" if AR_LETTER.search(key) else "latin",
                                      words=len(key.split()), sources=[], attia_category="", category="", note=""))
        if source not in r["sources"]:
            r["sources"].append(source)
        r["attia_category"] = r["attia_category"] or attia_cat
        r["category"] = r["category"] or ours
        r["note"] = r["note"] or note

    for t in lines("ldnoobw_v2_ar.txt"): add(t, "ldnoobw_v2")
    for t in lines("ldnoobw_v1_ar.txt"): add(t, "ldnoobw_v1")
    for t in lines("mubarak_obscene.txt"): add(t, "mubarak2017")
    for t in lines("uxbert_ar.txt"): add(t, "uxbert")
    for t in lines("profanity_csv_Arabic.csv"): add(t, "profanity_csv")
    for t, sec, title in parse_attia((SRC / "attia_README.md").read_text(encoding="utf-8")):
        add(t, "attia", f"{sec}. {title}", ATTIA_TO_OURS.get(sec, ""))
    for t, rating in parse_cuss((SRC / "cuss_ar-latn.js").read_text(encoding="utf-8")):
        add(t, "cuss", note=f"cuss sureness {rating}")

    out = sorted(rows.values(), key=lambda r: (r["script"], r["key"]))
    with open(HERE / "ar_combined.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t")
        w.writeheader()
        for r in out:
            w.writerow(r | {"sources": ",".join(r["sources"])})
    return out


def test():
    assert normalize("  كَلْبٌ ") == "كلب"
    assert normalize("كـــلب") == "كلب"                       # tatweel
    assert normalize("أحمق") == normalize("احمق") == "احمق"   # hamza forms
    assert normalize("حقيرة") == "حقيره" and normalize("مستشفى") == "مستشفي"
    assert normalize("﻿Shit ") == "shit"
    assert normalize("#افلام_سكس") == "افلام سكس" and normalize("ibn el-kalb") == "ibn el kalb"
    sample = ("x\n# Offensive Word Categories\n### 5. Animal\n* **بقرة / بقر (Baqara / Baqar):** Cow.\n#### A. Sub\n"
              "* **كلب (Kalb):** Dog.\n* **(صوت) عورة (Sawt Awra):** x\n")
    assert parse_attia(sample) == [("بقرة", "5", "Animal"), ("بقر", "5", "Animal"), ("كلب", "5", "Sub"),
                                   ("صوت عورة", "5", "Sub")]
    assert parse_cuss("export const cuss = {\n  '3ars': 2,\n  kalb: 1,\n}") == [("3ars", "2"), ("kalb", "1")]
    print("selftest ok")


if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
    else:
        rows = build()
        by = lambda k: {v: sum(1 for r in rows if r[k] == v) for v in sorted({r[k] for r in rows})}
        print(len(rows), "unique terms | by script:", by("script"), "| by category:", by("category"))
