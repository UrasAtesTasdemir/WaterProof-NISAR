# WaterProof — release readiness (final release pass, 2026-11-15)

Local release state only: not deployed, not submitted, no remote updated. Git tag `waterproof-final-release-2`
(the earlier tag `waterproof-final-release` points to the state before path masking).

## Verified

- **Automated tests:** `.venv/bin/python -m unittest discover -s tests` → 268 run, 267 passed, 0 failed, 1 skipped (the
  optional live-network test, which runs only with `NISAR_LIVE_TEST=1`). Warnings: library `PendingDeprecationWarning`s
  only (matplotlib `set_bad`, affine `*` → `@`).
- **Scientific data unchanged:** SHA-256 of all 545 files under `data/` (excluding the git-ignored `data/live_cache/`)
  recorded before this pass and re-verified after it: identical except the 16 masked logs listed below. No metric was
  recomputed or edited; labels only.
- **Evidence scopes:** one source of truth (`src/evidence_scope.py`): Louisiana research exploration · case-specific
  evaluation (exact saved NISAR products, dates and grid only; also the saved Thailand pre-event control pair) ·
  exploratory selection (everything else). Same label on screen and in exported notes.
- **Browser walkthrough** (local Streamlit, 1280×720 and 375×812): brand top-left; guided Thailand example; candidate
  map 25.67 km² with case-specific scope and pre-event control warning (3.14 / 5.19 km²); reference-comparison page with
  "Where the Method Works — and Where It Struggles", dates, offsets, evaluated area, maps and expandable provenance and
  control evidence; 3D globe renders and rotates by drag; English ↔ Turkish; light ↔ dark; review-note export returned a
  Markdown file with the scope text and dates; About page ends with the centred NASA data-source attribution in both
  languages and at phone width. No server errors.

## Corrected in this pass

- A crash introduced mid-pass (Researcher workflow: shadowed `scope_text` import).
- Blanket or over-strong wording ("Flood map (validated rule)", "nothing here has been checked", Louisiana-only limits
  presented as app-wide) → scope-specific wording in EN and TR.
- Thailand/Gandak scores are no longer shown on unrelated Explore selections.
- Selection reason and "ranking is not a risk score" shown on screen and in the note.
- Precise data provenance beside the required attribution (Sen1Floods11 is not a NASA source; DSWx inputs).
- Window-size control now shows a demo place's real window (10 km for Thailand).
- Hidden glossary tooltips no longer widen the page on phones.
- README rewritten; usability protocol aligned with the requested task (no sessions run).

- **Local paths masked:** the home path appeared in 16 saved test/environment logs under `data/`. It was replaced by
  `<project>` / `<home>` (344 replacements); `data/masked_logs.json` records each file's original and masked SHA-256.
  Exactly these 16 files changed; all other data files are identical. Historical hash records were left unchanged; the
  three tests that verify them accept a masked log only through the registry.
- **Git history still contains the unmasked logs** in earlier commits. Publishing the full history would expose the
  path; see "Before publishing" below.

## Before publishing

Push either a fresh history that starts from the release commit (e.g. a single squashed/orphan commit), or rewrite
history to drop the old log versions. Both change git history and were not done here.

## Not verified / known limitations

- Hosted deployment (memory, cold start, package install) — not attempted.
- No real-user usability sessions.
- Live reads of new places were verified earlier in development, not repeated in this pass.
- Scientific limits: three scenes in two regions; Thailand tracks are not independent; Gandak agreement is low
  (F1 0.24); DSWx references disagree; Louisiana findings are not validated; thresholds are exploratory.
