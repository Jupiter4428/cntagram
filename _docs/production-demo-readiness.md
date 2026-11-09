# CN331 Final Evaluation — Production Readiness Checklist

This is an evidence checklist, **not** a claim that the deployment has passed.

## 30 points — Functional completeness
- [ ] Open https://cntagram-h195.onrender.com/ from a fresh browser.
- [ ] With test accounts only, demonstrate registration validation, PDF upload, moderator approval, search and protected preview/download.
- [ ] Demonstrate invalid upload/duplicate, unapproved exam and unauthenticated PDF access.
- [ ] Record a backup demo video of the same cloud deployment.

## 25 points — Architecture
- [ ] Show C4 Context and Container diagrams from `_docs/architecture/c4.md`.
- [ ] Show a concrete service using `transaction.atomic` and selector using `select_related` / `prefetch_related`.
- [ ] Show evidence of N+1 regression tests (e.g. `assertNumQueries`).

## 25 points — Testing and security
- [ ] Capture a green GitHub Actions CI run on the actual `main` commit presented, with test count and coverage >= 80%.
- [ ] Review Render environment variables **without copying secret values into screenshots**.
- [ ] Run `python scripts/check_production_readiness.py` in a secure environment with the same configuration as Render; the helper checks configuration only and prints no secret values.
- [ ] Confirm `DEBUG=False`, HTTPS, secure cookies and authorized PDF delivery in the live service.
- [ ] Confirm whether Render uses a persistent disk for PDF files; local filesystem alone is not proof of persistence.
- [ ] Perform an isolated PostgreSQL and PDF backup/restore rehearsal **without modifying the live database**, documenting evidence for Issue #192.

## 20 points — Presentation
- [ ] Rehearse 12 minutes of presentation + 5 minutes Q&A (17 minutes total).
- [ ] Prepare speakers, actual GitHub Project board screenshots, C4 diagrams and CI evidence.
- [ ] Label open PRs and unimplemented features clearly; never describe them as live Production features.

## Notes
The readiness helper does not connect to Render, verify HTTPS endpoints, inspect disk mounts, or run a restore. Those require independent, authorized operational checks.
