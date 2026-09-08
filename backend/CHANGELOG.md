# Changelog

## Phase 0 — Bootstrap (2026-09-08)

- Project structure, `pyproject.toml`, configuration via pydantic-settings.
- FastAPI app with structured logging, request-id + access-log middleware,
  CORS, centralized error envelope, `/api/v1/health` and `/api/v1/version`.
- Test harness (pytest + pytest-asyncio + httpx ASGI client).

## Phase 1 — Database + migrations

- SQLAlchemy 2 async models for all Phase 1 entities (profiles, goals,
  training, accessibility, notifications, equipment, exercises, check-ins,
  workout plans/exercises/explanations, sessions) plus Phase 2 weekly
  summaries and local `auth_users` (mock auth).
- Alembic with an initial metadata-based migration.

## Phase 2 — Auth

- `POST /auth/signup|login|refresh|forgot-password|logout`.
- `get_current_user` dependency; Supabase JWKS verification for supabase mode;
  mock mode with PBKDF2-hashed local accounts and HS256 JWTs.
- Lazy profile creation; 401s for invalid tokens; ownership isolation tested.

## Phase 3 — Onboarding / Profile

- `GET/PATCH /me` and `GET/PUT /me/goals|training-profile|accessibility|
  equipment|notifications` plus `POST /me/onboarding/complete` with structured
  missing-fields validation. Equipment replacement is transactional.

## Phase 4 — Catalog

- Idempotent seed: 13 equipment items, 45 exercises with muscle groups,
  movement patterns, difficulty, rest, and equipment requirements.
- `GET /catalog/equipment`, `GET /catalog/exercises` (filters), and
  `GET /catalog/exercises/{id}`.

## Phase 5 — Check-Ins

- `POST /check-ins` (one per local day, 409 on repeat), `GET /check-ins/today`,
  `GET /check-ins`, `GET/PUT /check-ins/{id}` (PUT restricted to today).
- Canonical body-region validation, score bounds 1..10.

## Phase 6 — Deterministic Workout Engine

- Recovery score, intensity selection with caps, soreness exclusion/
  deprioritization with explicit region->muscle mapping, goal templates, rep
  ranges, experience volume, equipment filter, movement-balance slots, recent
  history de-prioritization, duration estimation and fitting.
- Plan validator with fallback retry; `POST /workouts/generate` (idempotent,
  concurrent-safe), `GET /workouts/today|list|{id}`.
- `rule_trace` persisted with every plan (`rules-v1`).

## Phase 7 — AI Explanation

- Provider protocol with Gemini-compatible and deterministic mock adapters.
- Short explanations generated from `rule_trace` only, validated
  (length/medical-language/foreign-exercise checks), with deterministic
  template fallback so generation never fails when the AI is unavailable.
- Explanations persisted once and re-read without re-calling the provider.

## Phase 8 — Workout Sessions

- `POST /workout-sessions` (start), `GET /{id}`, `POST /{id}/complete` (RPE,
  modifications, soreness, notes; plan marked completed; daily summary
  returned), `POST /{id}/quit` (session kept, plan re-available).

## Phase 9 — Home + Progress

- `GET /home` aggregation endpoint (fan-out reduction).
- `GET /progress` with consistency score, streak, 7-day counts, and
  non-fabricated energy/recovery trends; `GET /progress/workouts` and
  `/progress/check-ins` history lists.

## Phase 10 — Weekly + Deep Insight (Phase 2)

- Weekly engine: deterministic aggregation of consistency, recovery, energy,
  soreness, RPE, and intensity mix into weekly summaries with planned
  adjustments (`volume_direction`, `intensity_cap`, `focus_notes`).
- `GET /weekly/current|{week_start}`, `POST /weekly/generate`,
  `GET /weekly/{week_start}/insight`.
- Workout Deep Insight: five structured sections, generated once and persisted
  (`GET /workouts/{id}/insight`).

## Phase 11 — Deployment

- Dockerfile (slim, non-root, `$PORT`-aware) and docker-compose (API + Postgres).
- GitHub Actions CI: install, Ruff, tests, migration check against Postgres.
- README, `docs/frontend-api.md`, `DECISIONS.md`, test-user script.
