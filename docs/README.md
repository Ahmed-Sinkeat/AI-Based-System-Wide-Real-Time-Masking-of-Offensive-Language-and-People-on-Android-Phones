# Docs: start here

**Project:** an Android app that hides bad language and images of people on the screen, across the apps people use every day (limits: SRS §5). Everything runs on the phone.

**Release order:** v1 bad-language text (Arabic + English: word list + our own small text model) → v2 text inside images → v3 big people → v4 medium people. **Graduation scope is v1–v4**; v5 small people is a bonus; v6 video is after graduation.

**Project rule:** every decision, change, or obstacle gets a dated entry in [`asbuild.md`](asbuild.md).

**Status (2026-10-18):** research done; people-model tests done on laptop and phone (GPU ~205 ms per screen at 640 px); app design agreed; plan reset to six months (deadline around mid-April 2027) with text inside images (v2) and video (v6) added. No app code yet. **Next step: v1-a, the app skeleton** (see [`issue.md`](issue.md)).

## Current (Android)

| File | What it is |
|---|---|
| [`roadmap.md`](roadmap.md) | **Plan by week**: phases v1 → v6, workstreams, exit criteria, report plan, schedule risks |
| [`research-methods.md`](research-methods.md) | **Research questions, methods (M1–M7), evaluation plan, validity, ethics, AI-tool use, references (IEEE)** |
| [`research-en.pdf`](research-en.pdf) | **Research and related work as one readable page** |
| [`app-design-v1.md`](app-design-v1.md) | **App design (agreed)**: tech stack, architecture, screens inside the app, covers / notification / tile outside it, data, errors, testing, things to verify early |
| [`asbuild.md`](asbuild.md) | **As-built log**: every decision, why, alternatives, and what got in the way (add an entry each time) |
| [`issue.md`](issue.md) | **Issues**: open problems and checks with next actions, by priority and stream; closed issues with their fix |
| [`investigation-android-v1.md`](investigation-android-v1.md) | How it works on Android: text filter (§3), people (§4–§7), limits, the competing HaramBlur extension and app (§9), plan (§10), useful resources (§11) |
| [`p0-results-android-v1.md`](p0-results-android-v1.md) | People-model test results on the phone (for v3–v5), what broke, what to re-run |
| [`p0c-results-text-v1.md`](p0c-results-text-v1.md) | **Text model on the phone** (P0c step 1, quick): feasible: only bert-mini-arabic is within target (~16 ms / ~38 MB); bert-medium, e5-small too heavy |
| [`srs-en.pdf`](srs-en.pdf), [`srs-ar.pdf`](srs-ar.pdf) | Requirements (SRS v3.0, ISO/IEC/IEEE 29148 structure, v1 to v6), English and Arabic |
| [`Initial-Project-Proposal.pdf`](Initial-Project-Proposal.pdf) | Proposal (Arabic): **bad language + people** on **Android** |
| [`../wordlists/`](../wordlists/README.md) | Combined Arabic bad-word list (1 906 terms from 7 sources) + build script. Raw start for v1-c. |

## Plan B (Linux, paused)

| File | What it is |
|---|---|
| [`investigation-linux-v1.md`](investigation-linux-v1.md) | The Hyprland desktop design |
| [`p0-results-linux-v1.md`](p0-results-linux-v1.md) | Laptop tests. The model accuracy parts still apply to Android. |
| `srs-linux-en.*`, `srs-linux-ar.*` | The old SRS v1.0 (Linux) |

PDFs are printed from the HTML files with headless Chromium:
`chromium --headless=new --no-pdf-header-footer --virtual-time-budget=8000 --print-to-pdf=out.pdf file://$PWD/in.html`
