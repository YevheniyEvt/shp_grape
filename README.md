# Vineyard website

Grape variety catalog with ordering of cuttings and seedlings.

- Backend: Django 6.1 + Django REST Framework, PostgreSQL 17
- Frontend: Next.js 16 (React, TypeScript), Tailwind CSS, shadcn/ui
- Languages: Ukrainian (default), English; translations in Django `.po` files

## Requirements

Python 3.14 with [uv](https://docs.astral.sh/uv/), Node.js 24, Docker, [just](https://just.systems/),
GNU gettext (`makemessages` / `compilemessages`).

## Quick start

```bash
cp .env.example .env                                  # then set SECRET_KEY
cp frontend/.env.local.example frontend/.env.local
just setup                                            # dependencies, git hooks, database, migrations
just run                                              # API: http://127.0.0.1:8000/api/docs/
just front                                            # site: http://localhost:3000
```

Run `just` to see all commands. `just check` runs everything CI checks.

## Translations

UI strings are written in English in code (`gettext` / `t()` in the frontend), then
`just messages` extracts them into `locale/<lang>/LC_MESSAGES/{django,djangojs}.po`,
and `just compilemessages` compiles them.
