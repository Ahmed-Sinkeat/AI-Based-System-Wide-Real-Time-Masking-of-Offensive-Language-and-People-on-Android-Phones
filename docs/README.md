# HaramBlurr docs: start here

**Project:** an Android app that hides bad language and images of people on the screen, in every app. Everything runs on the phone.

**Release order:** v1 bad-language text (Arabic + English) → v2 big people → v3 medium people → v4 small people.

**Project rule:** every decision, change, or obstacle gets a dated entry in [`asbuild.md`](asbuild.md).

**Status (2026-10-07):** research done, people-model tests done (the phone speed test is half done). App design agreed (`app-design-v1.md`). No app code yet. **Next step: Phase 0 housekeeping, then v1-a, the app skeleton** (see `issue.md` for blockers).

## Current (Android)

| File | What it is |
|---|---|
| [`roadmap.md`](roadmap.md) | **Plan by week**: phases v1 → v4, workstreams, exit criteria, report plan, schedule risks |
| [`research-methods.md`](research-methods.md) | **Research questions, methods (M1–M6), evaluation plan, validity, ethics, AI-tool use, references (IEEE)** |
| [`app-design-v1.md`](app-design-v1.md) | **App design (agreed)**: tech stack, architecture, screens inside the app, covers / notification / tile outside it, data, errors, testing, things to verify early |
| [`asbuild.md`](asbuild.md) | **As-built log**: every decision, why, alternatives, and what got in the way (add an entry each time) |
| [`issue.md`](issue.md) | **Issues**: open problems and checks with next actions, by priority and stream; closed issues with their fix |
| [`investigation-android-v1.md`](investigation-android-v1.md) | How it works on Android: text filter (§3), people (§4–§7), limits, HaramBlur extension + Android app (§9), plan (§10), useful resources (§11) |
| [`p0-results-android-v1.md`](p0-results-android-v1.md) | People-model test results (for v2–v4), what broke, what to re-run |
| `srs-en.html` / `.pdf`, `srs-ar.html` / `.pdf` | Requirements (SRS v2.1, v1 to v4), English and Arabic |
| `proposal-ar.html` → `Initial-Project-Proposal.pdf` | Proposal (Arabic): **bad language + people** on **Android** |
| `cover.html` | Report cover page |
| [`../wordlists/`](../wordlists/README.md) | Combined Arabic bad-word list (1 906 terms from 7 sources) + build script. Raw start for v1-c. |

## Plan B (Linux, paused)

| File | What it is |
|---|---|
| [`investigation-linux-v1.md`](investigation-linux-v1.md) | The Hyprland desktop design |
| [`p0-results-linux-v1.md`](p0-results-linux-v1.md) | Laptop tests. The model accuracy parts still apply to Android. |
| `srs-linux-en.*`, `srs-linux-ar.*` | The old SRS v1.0 (Linux) |

## Old drafts

| File | Note |
|---|---|
| `ha.pdf` | An earlier proposal draft (people only). The current one is `Initial-Project-Proposal.pdf`. |

PDFs are printed from the HTML files with headless Chromium:
`chromium --headless=new --no-pdf-header-footer --virtual-time-budget=8000 --print-to-pdf=out.pdf file://$PWD/in.html`
