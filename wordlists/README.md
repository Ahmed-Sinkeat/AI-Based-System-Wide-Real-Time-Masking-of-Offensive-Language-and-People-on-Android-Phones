# Arabic bad-word list (combined)

`ar_combined.tsv` = every Arabic list we found, merged and de-duplicated. **It is a raw starting point, not the final v1 list.** The team must review it (see below).

Rebuild: `python3 build_ar.py` · Self-check: `python3 build_ar.py --test`

## What is in it (built 2026-10-06)

| | Count |
|---|---|
| Unique terms | **1 906** |
| Arabic script | **947** (680 single words, 267 phrases) |
| Latin script (Arabizi, e.g. "ibn el kalb") | 959 — **not for v1** (v1 = standard Arabic) |
| Arabic terms found in 2 or more lists | 147 |
| Arabic terms with a suggested category | 371 (all from Attia) |

## Sources

| Source (`sources` column) | File in `sources/` | Terms | Only in this list | License |
|---|---|---|---|---|
| `ldnoobw_v2` — LDNOOBW V2 | `ldnoobw_v2_ar.txt` | 1 284 (mostly Arabizi) | 887 | CC0 |
| `mubarak2017` — Mubarak, Darwish, Magdy 2017 (QCRI), obscene words and hashtags | `mubarak_obscene.txt` | 415 | 341 | "freely available for research" (paper) |
| `attia` — Mohammed Attia 2025, categorized lexicon | `attia_README.md` | 371 | 239 | **none stated: ask the author before publishing** |
| `profanity_csv` — 4troDev/profanity.csv | `profanity_csv_Arabic.csv` | 48 | 46 | MIT |
| `ldnoobw_v1` — LDNOOBW (Shutterstock) | `ldnoobw_v1_ar.txt` | 38 | 0 | CC-BY-4.0 (credit it) |
| `uxbert` — uxbertlabs | `uxbert_ar.txt` | 16 | 1 | MIT |
| `cuss` — words/cuss, Arabic in Latin letters | `cuss_ar-latn.js` | 245 | 1 | MIT |

Downloaded 2026-10-06 from:
- https://raw.githubusercontent.com/LDNOOBWV2/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words_V2/main/data/ar.txt
- http://alt.qcri.org/~hmubarak/offensive/ObsceneWords.txt
- https://raw.githubusercontent.com/mohammedattia/arabic-offensive-words/main/README.md
- https://raw.githubusercontent.com/4troDev/profanity.csv/main/Arabic.csv
- https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/ar
- https://raw.githubusercontent.com/uxbertlabs/arabic_bad_dirty_word_filter_list/master/arabic-profanity-bad-words-dictionary.txt
- https://raw.githubusercontent.com/words/cuss/main/ar-latn.js

If Attia says no: delete the rows whose `sources` is exactly `attia`, and clear `attia_category`/`category` on the others.

## Columns

| Column | Meaning |
|---|---|
| `key` | Cleaned form used for matching: no tashkeel or tatweel, أإآ→ا, ى→ي, ة→ه, `#` `_` `-` `.` → space, lowercase |
| `term` | The term as first seen |
| `script` | `arabic` or `latin` |
| `words` | 1 = single word, 2+ = phrase |
| `sources` | Which lists contain it |
| `attia_category` | Attia's original category (if he lists it) |
| `category` | **Suggested** category for us: `swearing` / `sexual` / `insult` (from Attia's section). Empty = not sorted yet. No source gives `blasphemy`: the team writes that part. |
| `note` | e.g. Arabizi "sureness" rating from cuss |

## What the team must do (step v1-c)

1. **Keep standard Arabic** for v1. Mark dialect-only terms (most lists are Egyptian / Levantine / Gulf) as `later`.
2. **Sort every kept term** into swearing / sexual / insult / blasphemy. Add the blasphemy phrases ourselves.
3. **Remove or move to "phrase only" anything that is a normal word in other contexts.** The lists contain words such as أمك / أختك (your mother / your sister), كافر, حمار, كلب, عورة. As single words they would cover normal text, news, and Quran. Keep them only inside phrases (e.g. "يا كلب", "ابن الكلب") or in the strict insult list.
4. Test on clean text (news, Quran, normal chats) and on real offensive comments (investigation §3.4), then fix the list.
