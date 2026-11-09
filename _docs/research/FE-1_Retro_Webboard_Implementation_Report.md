# FE-1 Implementation Report — Retro Webboard Base Layout & Theme

**Project:** CNTAGRAM — CN331 Web Board
**Issue:** [#38 — FE-1 Retro Webboard Base Layout & Theme](https://github.com/Jupiter4428/cntagram/issues/38)
**Repository:** [Jupiter4428/cntagram](https://github.com/Jupiter4428/cntagram)
**Branch:** `feature/issue-38-retro-layout`
**Commit:** `c78b11742c3e9c360a3f345fdc35d128a3570864`
**Commit subject:** `feat(ui): add retro webboard base layout and theme`
**Commit body:** `Refs #38`
**Report date:** 14 October 2026
**Status:** Merged into `main` and deployed to Production; retro widgets and community webboard were subsequently promoted to live features (PR #180, #202, #222, #226, #232, #233).

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
- Marked illustrative content and counters as **DEMO / illustrative** so that they are not mistaken for live data. These widgets (archive, music player, visitor counter, directory, badges) render on the Home page only (`includes/_home_widgets.html`); the shared layout carries no DEMO content (#88).
- Did not implement real audio playback or visitor analytics.

### 2.4 Authentication pages

- Updated Login, Register, and Vault templates to share the retro visual system.
- Separated authentication-page content from the full Home sidebar using `auth_base.html` and `_auth_help.html`.
- Kept POST-only logout with CSRF, login CSRF, safe redirects, guest protection, session behavior, and rate limiting unchanged.
- Register remains a placeholder inherited from the US-2 scope.

### 2.5 Promotion of Retro Widgets to Live Functional Features (PR #180 / Refs #89, #161)

Following the initial layout foundation, four primary retro widgets were promoted from illustrative/DEMO shells into fully functional, live features:
- **Interactive BGM Player (US-39, Issue #161)**: Added an audio playback engine (`static/js/bgm_player.js`) supporting play/pause, seekbar tracking, volume/mute adjustment, track switching, and a playlist of nostalgic 2000s and 8-bit tracks.
- **Interactive Community Shoutbox (US-36, Issue #89)**: Implemented server-side cache rolling history (up to 30 messages), authenticated user author attribution `[<Dept>] <Nickname>`, and seamless AJAX submission without full-page reloads (`static/js/home_widgets.js`).
- **Live Weekly Community Poll (US-37, Issue #89)**: Added atomic cache-backed voting, dynamic percentage calculations, session-based vote tracking, view toggling, and instant non-refresh AJAX updates.
- **Real-time Retro Visitor Counter (US-38, Issue #89)**: Promoted the 6-digit LCD counter from a mock placeholder to real-time atomic visit counting incrementing on each homepage visit, removing decorative disclaimers.

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

## 5. Evolution from FE-1 Base Layout to Live Features

In the initial FE-1 commit (`c78b117`), community widgets were visual shells. In Sprint 3, the following capabilities were implemented and merged into `main`:

- **Live Community Webboard (`webboard` app)**: Full CRUD for threads and replies (`BoardCategory`, `Thread`, `Post`), course tagging, pin/lock/delete moderation, thread/post editing with edited indicator (`is_edited`), MSN Messenger emoticon parser (`webboard/emoticons.py`), and safe `[img]...[/img]` / external GIF embedding.
- **Live Home Widgets (`accounts` app)**: Database-backed Shoutbox (`ShoutboxMessage`) and Weekly Poll (`PollVote`) with AJAX submission, atomic 6-digit LCD visitor counter, and interactive retro BGM player (`static/js/bgm_player.js`).

---

**Summary:** The FE-1 retro webboard base layout, theme, and subsequent interactive community features are merged into `main` and live in production.
