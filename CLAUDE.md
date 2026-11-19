# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules
- Answer in Ukrainian.
- All documentation in code like docstrings and comments written in English.
- Planning context lives in @.context (gitignored, like `.claude/`). When the user says "починаємо етап N" or "завершуємо етап N", use the `stage` skill.

## Environment

- Windows 11 + PyCharm. Django sits at the repo root and the config package `shp_grape/` must keep its name, because PyCharm's Django facet points to `shp_grape/settings.py` and `manage.py`.
- Python 3.14 with packages managed by **uv** (`pyproject.toml`, `uv.lock`, `.venv` at the root). Run Python tools with `uv run …`.
- Node 24 for the Next.js frontend in `frontend/`.
- PostgreSQL 17 runs in Docker (`docker-compose.yml`, service `db`). Docker Desktop must be running.
- `just` and GNU gettext are installed with winget, at `%LOCALAPPDATA%\Programs\gettext-iconv\bin`. When Git Bash cannot find them, add that folder and `%LOCALAPPDATA%\Microsoft\WinGet\Links` to `PATH`.
- Configuration comes from `.env`; copy `.env.example`. The frontend reads `frontend/.env.local`; copy `frontend/.env.local.example`.

## Commands

Prefer the `justfile` recipes; `just` lists them all. Add any new recurring command there.

```
just setup                 # uv sync, npm ci, git hooks, start db, migrate, compilemessages
just up / down             # PostgreSQL in Docker
just run                   # Django at http://127.0.0.1:8000 (/api/docs/ = Swagger, /admin/)
just front                 # Next.js at http://localhost:3000 (needs the Django API running)
just migrate / makemigrations [app]   # migrate also runs createcachetable
just test [pytest args]    # e.g. just test apps/core/tests/test_api.py -k health
just test-front            # Vitest
just lint / fmt            # ruff + eslint + tsc + prettier
just messages              # extract strings into locale/*/LC_MESSAGES/{django,djangojs}.po
just compilemessages       # .po -> .mo (.mo files are not committed)
just gen-api               # regenerate frontend/src/types/api.ts from the running API
just check                 # everything CI runs
just bump                  # release: version + CHANGELOG + tag (commitizen)
```

To run a single test without `just`, use `uv run pytest path/to/test_file.py::test_name`. pytest runs with `-n auto --reuse-db`; add `--create-db` after changing migrations. To run one frontend test file: `cd frontend; npx vitest run src/i18n/gettext.test.ts`.

## Architecture

### Backend (Django REST API)
- `shp_grape/settings.py` reads `.env` via django-environ. `settings_test.py` (used by pytest) switches to an MD5 hasher, in-memory file storage, the locmem cache and the locmem mailer. The cache is `DatabaseCache` (no Redis in the MVP). Email uses the Django 6.1 `MAILERS` setting.
- Apps live in `apps/` (`core`, `catalog`, `content`, `orders`). `orders` is still an empty skeleton.
- Each app keeps views and serializers thin, with logic in `services.py` / `selectors.py`. Tests live in `apps/<app>/tests/`, and the shared fixtures (`api_client`, `user`, `language`) are in the root `conftest.py`.
- `apps/core` holds `TimeStampedModel`, `SlugNaturalKeyManager`, `slugs.py` (`AutoSlugMixin`), `richtext.py` (`RichTextField`, django-prose-editor with nh3 sanitizing), the migration that enables the `pg_trgm` and `unaccent` extensions, and these endpoints:
  - `/api/health/` returns the status, the database check and the version;
  - `/api/i18n/languages/` lists the site languages;
  - `/api/i18n/<lang>/` serves the `djangojs` catalog (JSONCatalog).
- The project version comes from `[project].version` in `pyproject.toml` (`apps/core/version.py`).
- `ADMIN_URL` is configurable through the environment. `AdminLanguageMiddleware` always shows the admin in `ADMIN_LANGUAGE_CODE` (uk); the API follows `Accept-Language`. Shared admin CSS is `apps/core/static/core/admin.css`. `templates/admin/base_site.html` shows the project version next to the site name.
- `apps/catalog`: `Variety` (+ `VarietyPhoto` with imagekit WebP renditions `thumb`/`medium`/`large`, generated on save, and `VarietyVideo`) and the reference lists `RipeningPeriod`, `BerryColor`, `PulpConsistency`, `Taste`, `GrowthVigor`. Translated fields are registered in `translation.py`; `first_letter_<lang>` is computed in `save()`. Search, range overlap, similar varieties and letters live in `selectors.py`; the view counter and bulk photo upload live in `services.py`; filters are in `filters.py`. Factories are in `apps/catalog/tests/factories.py`. Endpoints under `/api/catalog/`:
  - `varieties/` (filters, `search`, `ordering`, `page`/`page_size`) and `varieties/<slug>/`;
  - `POST varieties/<slug>/view/`, `filters/`, `letters/`, `photos/random/?limit=`.
- Use `selectors.localized("name")` to sort or annotate by a translated field: modeltranslation stores missing translations as NULL, and it rewrites `Meta.ordering` into an explicit `order_by`.
- `apps/content`: so far only `SiteSettings` (django-solo singleton, default row from a data migration) with the page background: `show_background` and `background_image` (WebP rendition `background`). `GET /api/content/settings/` returns them; the frontend layout renders `SiteBackground` (`src/components/layout/site-background.tsx`), which tiles `public/images/grape-pattern.svg` when no photo is uploaded. Stage 5 adds the remaining fields and models.

### Frontend (`frontend/`, Next.js 16 App Router)
- **Next.js 16 differs from older versions.** Read `frontend/node_modules/next/dist/docs/` before using an unfamiliar API (see `frontend/AGENTS.md`):
  - `proxy.ts` replaces `middleware.ts`;
  - `cacheComponents` is on: cache data with `"use cache"` + `cacheLife`;
  - `next/root-params` provides the `lang` root param;
  - pages that should not be validated for instant navigation export `instant = false`.
- **Routing:** every route lives under `src/app/[lang]/`. `src/proxy.ts`, with its logic in `src/i18n/routing.ts`:
  - serves `uk` without a prefix by rewriting `/x` to `/uk/x`;
  - redirects `/uk/x` to `/x`;
  - serves `/en/x` as is;
  - honours the `NEXT_LOCALE` cookie.
- **Unknown URLs** hit `[lang]/[...rest]` and render the localized `not-found.tsx`.
- **i18n:**
  - UI strings use `t()` / `nt()` / `pt()` with English msgids. Never hardcode UI text.
  - Server Components call `getTranslator()` from `src/i18n/server.ts`; Client Components call `useT()` from `src/i18n/client.tsx`.
  - Translations come from Django's `djangojs.po`, through `/api/i18n/<lang>/`.
  - `uv run manage.py makemessages_frontend` (in `apps/core/i18n.py`) extracts the strings from TSX. Only literal string arguments are extractable.
  - Menu labels are built in `src/config/site.ts` via `getMainNav({ t })`.
- **UI:**
  - shadcn/ui (Radix, nova preset) components are in `src/components/ui/`, and layout pieces (header, footer, mobile menu, language switcher) in `src/components/layout/`.
  - Theme tokens (grape purple primary, leaf-green accent, warm background; Manrope/Lora fonts) are in `src/app/globals.css`.
- **API client:** `src/lib/api.ts` (`apiFetch`) sends `Accept-Language`. Generated API types are in `src/types/api.ts`.

### Conventions
- Translations:
  - DB content is translated with django-modeltranslation.
  - Static text uses gettext only. The `.po` files are the single source; there are no JSON message files.
  - Slugs are transliterated automatically from the Ukrainian name (KMU 2010), are unique, and never change when the object is renamed. Inherit `AutoSlugMixin` from `apps/core/slugs.py`.
- Reference data (lists like ripening periods, berry colours, tastes; a default `SiteSettings` row) is created by data migrations with uk + en values, wherever a model has sensible defaults. Freeze the values and slugs in the migration, use `get_or_create` by slug so admin edits survive, and make the reverse delete only unused rows. Example: `apps/catalog/migrations/0003_default_dictionaries.py`.
- Development and demo data come from `seed_demo` (`just seed`, `just seed-reset`; command in `apps/core/management/commands/`). Catalog demo data is frozen in `apps/catalog/demo.py` (invented varieties, no factory-boy: it is a dev-only dependency). The command is idempotent by slug and never touches existing or non-demo objects; `--reset` recreates only the demo objects. Own photos go to `fixtures/demo/photos/<slug>/` (record sources in `fixtures/demo/CREDITS.md`), otherwise Pillow draws placeholders. It also creates a superuser from `DJANGO_SUPERUSER_*`. Never scrape the source site.
- Tests:
  - All business logic must be covered by tests, as described in `.context/03-testing.md`.
  - Coverage must be at least 85% overall (enforced by pytest-cov) and at least 95% for services, selectors and utilities.
- Git:
  - Commits use Conventional Commits in English, checked by a commitizen commit-msg hook. Pre-commit also runs ruff, prettier and eslint.
  - Each stage gets a branch `stage/NN-<name>` with a PR to `main`. CI is `.github/workflows/ci.yml`.
  - There is one SemVer version, in `pyproject.toml` and mirrored in `frontend/package.json`.
- Monitoring (planned for stages 7–8, see `.context/04-monitoring.md`):
  - Sentry for the backend and frontend;
  - error alerts go to the admin's Telegram through `apps/core/monitoring.py` (deduplicated and rate-limited, disabled when no token is set);
  - never log customer personal data.
- Prefer existing Django and React libraries over custom code.
