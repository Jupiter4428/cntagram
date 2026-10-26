# FE-1 Implementation Report — Retro Webboard Base Layout & Theme

**Project:** CNTAGRAM — CN331 Web Board
**Issue:** [#38 — FE-1 Retro Webboard Base Layout & Theme](https://github.com/Jupiter4428/cntagram/issues/38)
**Repository:** [Jupiter4428/cntagram](https://github.com/Jupiter4428/cntagram)
**Branch:** `feature/issue-38-retro-layout`
**Commit:** `c78b11742c3e9c360a3f345fdc35d128a3570864`
**Commit subject:** `feat(ui): add retro webboard base layout and theme`
**Commit body:** `Refs #38`
**Report date:** 14 October 2026
**Status:** Implementation and documentation committed and pushed; FE-1 pull request not yet opened.

## 1. Objective

Develop the reusable frontend foundation for CNTAGRAM using Django Templates, Bootstrap 5, and custom CSS. The design combines an early-2000s Thai webboard / Blogger / hi5 / Xanga layout with Y2K and Frutiger Aero styling, incorporating Thammasat School of Engineering (TSE)-inspired colors.

This issue covers **base layout, theme, reusable UI modules, and demonstrative pages**, not implementation of new forum or analytics backend features.

## 2. Implemented Work

### 2.1 Reusable layout and navigation

- Updated `templates/base.html` with reusable page blocks including `body_class`, `layout_class`, and `sidebar`.
- Added `templates/auth_base.html` to give Login/Register pages a focused authentication layout.
- Added reusable Navbar, Sidebar, Footer, and Help partials.
- Integrated Django static asset loading via `STATICFILES_DIRS` and `{% static 'css/retro.css' %}`.
- Preserved named routes and authenticated/guest navigation.

### 2.2 Retro theme and home page

- Developed `static/css/retro.css` with Y2K-style chrome/plastic gradients, glossy tabs, metallic styling, decorative accents, and responsive layout rules.
- Used a **Blogger/Xanga-inspired community composition**: compact forum rows, date strips, post previews, metadata footers, and archive-style widgets.
- Retained the CNTAGRAM chrome wordmark, retro decorative graphics, and TSE-inspired red (`#8C191C`) and yellow (`#FFD04F`).
- Added an original SVG graphic at `static/img/cyber-orb.svg`.
- Added illustrative community content rather than connecting to unfinished backend features.

### 2.3 Widgets and retro decoration

- Added an archive tree based on year → semester → subject, implemented with accessible `<details>` / `<summary>` elements.
- Added marquee, stickers, 88×31-style badges, nostalgic microcopy, visitor-counter display, and music-player visual shell.
- Made secondary widgets collapsible to reduce mobile-page length.
- Marked illustrative content and counters as **DEMO / illustrative** so that they are not mistaken for live data.
- Did not implement real audio playback or visitor analytics.

### 2.4 Authentication pages

- Updated Login, Register, and Vault templates to share the retro visual system.
- Separated authentication-page content from the full Home sidebar using `auth_base.html` and `_auth_help.html`.
- Kept POST-only logout with CSRF, login CSRF, safe redirects, guest protection, session behavior, and rate limiting unchanged.
- Register remains a placeholder inherited from the US-2 scope.

## 3. Files Changed

**Modified (7):**

```text
accounts/templates/accounts/home.html
accounts/templates/accounts/login.html
accounts/templates/accounts/register.html
accounts/tests.py
materials/templates/materials/vault.html
portal/settings.py
templates/base.html
```

**Added (14):**

```text
static/css/retro.css
static/img/cyber-orb.svg
templates/auth_base.html
templates/includes/_archive.html
templates/includes/_auth_help.html
templates/includes/_badges.html
templates/includes/_digital_ephemera.html
templates/includes/_footer.html
templates/includes/_marquee.html
templates/includes/_music_player.html
templates/includes/_navbar.html
templates/includes/_sidebar.html
templates/includes/_stickers.html
templates/includes/_visitor_counter.html
```

**Total:** 21 files in the FE-1 commit; reported change size: 5,456 insertions and 60 deletions.

## 4. Validation and Test Results

The following results are taken from the final Codex implementation and commit reports:

| Check | Reported result |
|---|---|
| `python manage.py check` | Passed — 0 issues |
| `python manage.py test` | Passed — 22 tests |
| `python manage.py findstatic css/retro.css` | Asset found |
| `python manage.py makemigrations --check --dry-run` | No new migrations |
| `git diff --cached --check` | Passed |
| `git ls-files -u` | No unmerged index entries |
| Working tree after commit | Clean |

The 22 tests include existing authentication tests and additional frontend rendering tests. No changes to models, migrations, authentication services, or business logic were reported.

### Responsive QA

Final visual QA covered Home, Login, and Register at widths 390, 480, 768, 1024, and 1440 pixels.

| Viewport (px) | Reported document scroll width (px) | Horizontal overflow |
|---:|---:|---|
| 390 | 375 | None |
| 480 | 465 | None |
| 768 | 753 | None |
| 1024 | 1009 | None |
| 1440 | 1425 | None |

The reported 15-pixel difference is attributable to vertical scrollbar space. No clipped interactive elements were reported. The Home page at 390px remained approximately 3,742px tall due to retained content and widgets. Desktop Login height was reduced from approximately 2,081px to 966px.

> **Evidence:** Full-page screenshots were saved by Codex outside the repository at `C:\Users\USER\AppData\Local\Temp\cntagram-fe1-final-review\` for Home, Login, and Register at the five viewport widths listed above. Those temporary paths are not included in this Markdown file as embedded repository assets.

## 5. Scope Boundaries and Known Limitations

The following elements are **demonstration/UI only** and are not functional backend features:

- Community posts, post counts, category content, and metadata.
- Course archive subject entries.
- Visitor counter (not real analytics).
- Music-player shell (not connected to licensed audio).
- No post creation, comment/reply backend, guestbook, personalized themes, or user-uploaded stickers.

Additional non-blocking follow-up items:

- `static/css/retro.css` was reported to be about 103 KB with layered overrides; consider future CSS cleanup.
- `CONTRIBUTING.md` contains pre-existing conflict-marker text near line 831 inherited from base commit `3d391d5`; it was **not changed** as part of FE-1 and should be addressed separately by the team.
- Manual/automated review should be repeated if real content replaces demo data.

## 6. Git and Delivery Status

| Delivery step | Status |
|---|---|
| Implement frontend and run checks | Complete |
| Commit on FE-1 branch | Complete — `c78b117` |
| Push FE-1 branch to origin | Complete; local and remote reported 0 ahead / 0 behind |
| Prepare implementation documentation | This Markdown report prepared |
| Open FE-1 PR targeting `develop` | **Pending** |
| Peer review (minimum one reviewer) | **Pending** |
| Merge into `develop` / close Issue #38 | **Pending** |

**Dependency:** At last check, [US-2 PR #37](https://github.com/Jupiter4428/cntagram/pull/37) was still open and had not been merged into `develop`.

The FE-1 branch is based on the US-2 branch. Consequently, compared with `origin/develop` at `3d391d5`, it includes the two US-2 commits (`20d0d33`, `0cbc399`) as well as the FE-1 commit (`c78b117`). **Do not open the FE-1 PR to `develop` before resolving this dependency**, or the PR may include US-2 changes.

After US-2 is merged, fetch latest remote refs and inspect the commit ancestry. If US-2 was merged normally, the FE-1 PR should show only its FE-1 changes. If US-2 was squash-merged or rebased, prepare a clean branch from the updated `develop` and cherry-pick the FE-1 commit, then rerun tests before opening the PR.

## 7. Remaining Submission Checklist

- [x] Commit FE-1 implementation (`c78b117`)
- [x] Push `feature/issue-38-retro-layout`
- [x] Prepare FE-1 implementation report (`.md`)
- [x] Add the report to the appropriate repository documentation location, commit, and push it
- [ ] Wait for US-2 PR #37 to merge into `develop`
- [ ] Verify FE-1 branch diff against updated `develop`
- [ ] Open FE-1 pull request with `Closes #38`, report, screenshots, and test results
- [ ] Obtain required review and merge following team rules

---

**Summary:** FE-1 frontend implementation and documentation are complete, tested, committed, and pushed. The remaining work is the PR/review/merge workflow after the US-2 dependency is resolved.
