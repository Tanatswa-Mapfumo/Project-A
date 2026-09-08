# Adaptive Fitness Coach Backend — Codex Master Build Specification

**Document purpose:** This is the authoritative implementation brief for Codex (or another coding agent) to build the complete backend for the Adaptive Fitness Coach proof of concept.

**Source product specification:** `Gym_MVP_Restructured.docx`, Version 2.0 (2026-09-07).

**Target outcome:** A working, testable, deployable FastAPI backend with a PostgreSQL database, authentication, onboarding/profile APIs, daily check-ins, deterministic adaptive workout generation, workout sessions, progress analytics, AI-generated explanations, Phase 2 weekly summaries, OpenAPI documentation, tests, seed data, Docker support, and a staging deployment that a remote frontend developer can use.

---

# 0. Instructions to Codex

Treat this document as the primary engineering specification.

## 0.1 Working rules

1. If the repository is empty, bootstrap the project.
2. Implement the system in the phase order in section 24.
3. Do not redesign the public API casually after an endpoint has been implemented.
4. Keep the backend as a **modular monolith**, not microservices.
5. Use clear layers:
   - API/router
   - schemas
   - services/business logic
   - repositories/data access
   - database models
   - AI provider adapter
6. Keep deterministic workout logic separate from LLM explanation logic.
7. Never let the LLM directly write to the database or choose arbitrary exercises.
8. The LLM may only explain structured facts already produced by the deterministic engine.
9. Never commit secrets.
10. Every new endpoint must have:
    - request/response Pydantic models,
    - validation,
    - auth requirements,
    - service implementation,
    - tests,
    - OpenAPI documentation.
11. Every database schema change must have an Alembic migration.
12. Run the test suite before considering a phase complete.
13. Keep Phase 1 fully functional even if the AI provider is unavailable.
14. Implement graceful fallbacks for AI failures.
15. If a non-blocking implementation detail is not specified, make a sensible minimal decision and document it in `DECISIONS.md`.
16. Do not add large infrastructure such as Kubernetes, Redis, Kafka, Celery, or separate microservices unless a later requirement genuinely needs them.
17. Prefer simple, explicit, testable code over clever abstractions.
18. The final backend must work both:
    - locally,
    - on a public staging deployment.
19. Preserve backward compatibility for the frontend during active development whenever practical.
20. Finish each phase with a short entry in `CHANGELOG.md`.

## 0.2 Definition of success

A remote frontend developer must be able to:

1. create or log in to a test account,
2. complete onboarding,
3. submit a daily check-in,
4. generate a workout,
5. inspect why the workout was generated,
6. start and complete a workout session,
7. submit feedback,
8. view home/progress data,
9. call every endpoint through Swagger/OpenAPI,
10. do all of the above through a public HTTPS staging URL.

---

# 1. Product Context

The Adaptive Fitness Coach is an AI-driven mobile fitness application for general users pursuing:

- fat loss,
- muscle gain,
- strength,
- mobility.

The application adapts workouts using:

- user profile,
- training profile,
- accessibility preferences,
- daily recovery/check-in data,
- workout history,
- available equipment,
- time available.

The product uses two adaptation timescales:

### Daily micro-adjustment — Phase 1

Daily workouts adapt to:

- energy,
- sleep,
- mood,
- stress,
- soreness,
- pain,
- available time,
- recent history.

### Weekly macro-planning — Phase 2

Weekly summaries aggregate:

- session completion,
- consistency,
- recovery patterns,
- energy trends,
- progression signals,

and produce planned adjustments for the next week.

The backend must also support two levels of explanation:

1. **Short explanation** — one sentence.
2. **Deep Insight** — longer structured reasoning shown only when requested.

---

# 2. Scope

## 2.1 Phase 1 — Core MVP

Must implement:

- authentication,
- onboarding/profile persistence,
- goals,
- training profile,
- equipment preferences,
- accessibility preferences,
- notification preferences persistence,
- daily check-in,
- deterministic workout generation,
- daily micro-adjustment,
- workout plan storage,
- short AI explanation,
- workout retrieval,
- workout session start,
- workout session completion,
- post-workout RPE and notes,
- home dashboard aggregation,
- basic progress analytics,
- exercise/equipment catalogs,
- Swagger/OpenAPI,
- health endpoint,
- automated tests,
- local Docker support,
- staging deployment.

## 2.2 Phase 2 — Intelligence Layer

Implement after Phase 1 is stable:

- Deep Insight,
- weekly overview,
- weekly summary,
- weekly macro-adjustments,
- weekly Deep Insight,
- trend analytics,
- more advanced progression logic.

## 2.3 Out of scope for this backend version

Do not implement yet:

- nutrition,
- community/social features,
- human coach marketplace,
- payments/subscriptions,
- wearable integrations,
- video calling,
- complex ML training infrastructure,
- live real-time chat,
- push delivery infrastructure beyond storing notification preferences,
- admin dashboard unless needed for debugging.

---

# 3. Architecture

Use a modular monolith.

```text
Mobile/Web Frontend
        |
        | HTTPS + JSON + Bearer JWT
        v
+--------------------------------------+
|              FastAPI                 |
|                                      |
|  Auth verification                   |
|  User/Profile                        |
|  Check-Ins                           |
|  Workout Engine                      |
|  Session Tracking                    |
|  Progress                            |
|  Explanation Engine                  |
|  Weekly Engine                       |
+-------------------+------------------+
                    |
          +---------+---------+
          |                   |
          v                   v
   PostgreSQL/Supabase    LLM Provider
                         (provider adapter)
```

## Architectural rule

Workout logic must follow:

```text
User data
   |
   v
Deterministic adaptation rules
   |
   v
Workout plan builder
   |
   v
Workout plan validator
   |
   +---- invalid -> safe fallback / controlled error
   |
   v
Persist structured plan + rule trace
   |
   v
LLM explanation using ONLY rule trace + structured plan
```

The LLM must never be the sole source of workout decisions.

---

# 4. Technology Stack

Use:

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic v2
- pydantic-settings
- SQLAlchemy 2.x
- asyncpg
- Alembic
- PostgreSQL
- Supabase hosted PostgreSQL for staging
- Supabase Auth for identity
- httpx
- PyJWT or official Supabase client for token verification
- pytest
- pytest-asyncio
- Ruff
- Docker
- GitHub Actions

AI:

- provider abstraction,
- initial provider: Gemini-compatible adapter,
- optional future providers: OpenAI, Groq, local model.

Do not couple business logic to one AI provider.

---

# 5. Repository Structure

Create:

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── me.py
│   │       ├── catalog.py
│   │       ├── checkins.py
│   │       ├── workouts.py
│   │       ├── sessions.py
│   │       ├── home.py
│   │       ├── progress.py
│   │       ├── weekly.py
│   │       └── system.py
│   │
│   ├── core/
│   │   ├── auth.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── profile.py
│   │       ├── catalog.py
│   │       ├── checkin.py
│   │       ├── workout.py
│   │       ├── session.py
│   │       └── weekly.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── catalog.py
│   │   ├── checkin.py
│   │   ├── workout.py
│   │   ├── session.py
│   │   ├── progress.py
│   │   ├── weekly.py
│   │   └── common.py
│   │
│   ├── repositories/
│   │   ├── profiles.py
│   │   ├── checkins.py
│   │   ├── workouts.py
│   │   ├── sessions.py
│   │   ├── catalog.py
│   │   └── weekly.py
│   │
│   ├── services/
│   │   ├── onboarding.py
│   │   ├── checkins.py
│   │   ├── workout_generator.py
│   │   ├── adaptation_engine.py
│   │   ├── workout_validator.py
│   │   ├── explanation_engine.py
│   │   ├── sessions.py
│   │   ├── progress.py
│   │   └── weekly_engine.py
│   │
│   ├── rules/
│   │   ├── recovery.py
│   │   ├── soreness.py
│   │   ├── intensity.py
│   │   ├── exercise_filter.py
│   │   ├── duration.py
│   │   └── progression.py
│   │
│   └── ai/
│       ├── base.py
│       ├── gemini.py
│       ├── mock.py
│       └── prompts.py
│
├── alembic/
├── seeds/
│   ├── equipment.json
│   └── exercises.json
├── scripts/
│   ├── seed.py
│   └── create_test_user.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── DECISIONS.md
└── CHANGELOG.md
```

---

# 6. Configuration

Use `pydantic-settings`.

Required environment variables:

```env
APP_ENV=development
APP_NAME=Adaptive Fitness Coach API
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+asyncpg://...
DATABASE_URL_SYNC=postgresql://...

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

AUTH_MODE=supabase

AI_PROVIDER=gemini
GEMINI_API_KEY=
AI_MODEL=

FRONTEND_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8081

LOG_LEVEL=INFO
ENABLE_DOCS=true
```

Rules:

- `SUPABASE_SERVICE_ROLE_KEY` must never be exposed to the frontend.
- `.env` must be ignored.
- `.env.example` contains names only, never real secrets.
- `AUTH_MODE=mock` may be allowed only for local tests/dev.
- staging/production must use `AUTH_MODE=supabase`.

---

# 7. API Conventions

Base prefix:

```text
/api/v1
```

Use JSON.

Use ISO-8601 UTC timestamps.

Use UUIDs for persisted entities.

## 7.1 Authentication

Protected endpoint header:

```http
Authorization: Bearer <access_token>
```

## 7.2 Error format

All controlled API errors must use:

```json
{
  "error": {
    "code": "CHECKIN_NOT_FOUND",
    "message": "The requested check-in was not found.",
    "details": {}
  }
}
```

Do not return raw stack traces.

## 7.3 Common status codes

- `200` success
- `201` created
- `204` success, no body
- `400` bad request
- `401` unauthenticated
- `403` forbidden
- `404` not found
- `409` duplicate/conflict
- `422` validation/business rule failure
- `429` rate limited
- `500` unexpected internal error
- `503` dependency unavailable

## 7.4 Pagination

For list endpoints:

```text
?page=1&page_size=20
```

Response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

Cap `page_size` at 100.

---

# 8. Authentication Design

Supabase Auth is the identity provider.

The backend must never store raw passwords.

Implement these API endpoints for a single consistent frontend interface:

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/forgot-password
POST /api/v1/auth/logout
```

## 8.1 Signup

Request:

```json
{
  "email": "person@example.com",
  "password": "strong-password"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600,
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "person@example.com"
  }
}
```

If Supabase requires email confirmation, return a clearly documented state such as:

```json
{
  "requires_email_confirmation": true
}
```

## 8.2 Login

Same token response format.

## 8.3 Refresh

Request:

```json
{
  "refresh_token": "..."
}
```

## 8.4 Logout

Invalidate the current session through Supabase where supported.

## 8.5 Current user dependency

Implement:

```python
get_current_user()
```

It must:

1. parse Bearer token,
2. validate it with Supabase,
3. return authenticated user id + email,
4. reject invalid/expired tokens with 401.

Never trust a `user_id` sent by the client for protected resources.

---

# 9. Database Schema

Use PostgreSQL UUID primary keys and timezone-aware timestamps.

## 9.1 `profiles`

```text
id UUID PK
auth_user_id UUID UNIQUE NOT NULL
email VARCHAR(320) NOT NULL
name VARCHAR(120) NULL
age INTEGER NULL
height_cm NUMERIC(5,2) NULL
weight_kg NUMERIC(5,2) NULL
gender VARCHAR(80) NULL
country VARCHAR(100) NULL
onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Validation:

- age: reasonable positive integer if provided,
- height/weight: positive if provided,
- gender optional and user-defined.

Do not expose another user's profile.

---

## 9.2 `goal_profiles`

```text
id UUID PK
user_id UUID UNIQUE NOT NULL
primary_goal VARCHAR NOT NULL
secondary_goal VARCHAR NULL
target_metrics JSONB NOT NULL DEFAULT '{}'
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Allowed primary goals:

```text
lose_fat
gain_muscle
get_stronger
improve_mobility
```

---

## 9.3 `training_profiles`

```text
id UUID PK
user_id UUID UNIQUE NOT NULL
experience_level VARCHAR NOT NULL
preferred_days JSONB NOT NULL DEFAULT '[]'
session_length_minutes INTEGER NOT NULL
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Experience:

```text
beginner
intermediate
advanced
```

Allowed session length for MVP:

```text
15
30
45
60
```

---

## 9.4 `accessibility_profiles`

```text
id UUID PK
user_id UUID UNIQUE NOT NULL
screen_reader_enabled BOOLEAN DEFAULT FALSE
high_contrast BOOLEAN DEFAULT FALSE
simple_mode BOOLEAN DEFAULT FALSE
motion_reduced BOOLEAN DEFAULT FALSE
voice_enabled BOOLEAN DEFAULT FALSE
haptics_enabled BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Changes must persist immediately.

---

## 9.5 `notification_preferences`

```text
id UUID PK
user_id UUID UNIQUE NOT NULL
daily_checkin_reminders BOOLEAN DEFAULT TRUE
workout_reminders BOOLEAN DEFAULT TRUE
weekly_summary_alerts BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Only persistence is required in the POC. Actual push notification delivery is out of scope.

---

## 9.6 `equipment`

```text
id UUID PK
slug VARCHAR UNIQUE NOT NULL
name VARCHAR NOT NULL
category VARCHAR NOT NULL
active BOOLEAN DEFAULT TRUE
```

Initial categories may include:

- bodyweight,
- dumbbell,
- barbell,
- machine,
- cable,
- band,
- cardio,
- mobility.

---

## 9.7 `user_equipment`

```text
user_id UUID NOT NULL
equipment_id UUID NOT NULL
PRIMARY KEY (user_id, equipment_id)
```

---

## 9.8 `exercises`

```text
id UUID PK
slug VARCHAR UNIQUE NOT NULL
name VARCHAR NOT NULL
workout_type VARCHAR NOT NULL
movement_pattern VARCHAR NOT NULL
primary_muscle_groups JSONB NOT NULL
secondary_muscle_groups JSONB NOT NULL DEFAULT '[]'
difficulty VARCHAR NOT NULL
is_unilateral BOOLEAN DEFAULT FALSE
default_rest_seconds INTEGER NOT NULL
active BOOLEAN DEFAULT TRUE
metadata JSONB NOT NULL DEFAULT '{}'
```

Workout types:

```text
strength
cardio
mobility
mixed
```

Movement pattern examples:

```text
squat
hinge
horizontal_push
vertical_push
horizontal_pull
vertical_pull
carry
core
cardio
mobility
```

---

## 9.9 `exercise_equipment`

```text
exercise_id UUID NOT NULL
equipment_id UUID NOT NULL
PRIMARY KEY (exercise_id, equipment_id)
```

A bodyweight exercise can map to `bodyweight`.

---

## 9.10 `check_ins`

```text
id UUID PK
user_id UUID NOT NULL
checkin_date DATE NOT NULL
energy_score SMALLINT NOT NULL
soreness_map JSONB NOT NULL DEFAULT '{}'
mood_score SMALLINT NOT NULL
sleep_score SMALLINT NOT NULL
stress_score SMALLINT NOT NULL
time_available_minutes INTEGER NULL
pain_score SMALLINT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL

UNIQUE(user_id, checkin_date)
```

Scores are integers `1..10`.

`soreness_map` example:

```json
{
  "chest": 2,
  "shoulders": 3,
  "upper_back": 1,
  "lower_back": 2,
  "quads": 6,
  "hamstrings": 5,
  "glutes": 4,
  "calves": 1
}
```

Reject unknown values outside `0..10` or `1..10` according to the chosen region convention. Use one convention consistently and document it.

For MVP use `1..10` for explicitly reported regions and omit unreported regions.

---

## 9.11 `workout_plans`

```text
id UUID PK
user_id UUID NOT NULL
check_in_id UUID NOT NULL
plan_date DATE NOT NULL
type VARCHAR NOT NULL
intensity VARCHAR NOT NULL
duration_minutes INTEGER NOT NULL
goal_tags JSONB NOT NULL DEFAULT '[]'
short_explanation TEXT NULL
status VARCHAR NOT NULL DEFAULT 'generated'
generator_version VARCHAR NOT NULL
rule_trace JSONB NOT NULL DEFAULT '{}'
generation_metadata JSONB NOT NULL DEFAULT '{}'
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Statuses:

```text
generated
started
completed
cancelled
```

Intensity:

```text
low
moderate
high
```

Enforce one default generated plan per user/check-in unless regeneration is explicitly added.

---

## 9.12 `workout_exercises`

```text
id UUID PK
workout_plan_id UUID NOT NULL
exercise_id UUID NOT NULL
position INTEGER NOT NULL
sets INTEGER NULL
reps_min INTEGER NULL
reps_max INTEGER NULL
duration_seconds INTEGER NULL
load_kg NUMERIC NULL
rest_seconds INTEGER NULL
notes TEXT NULL
adaptation_tags JSONB NOT NULL DEFAULT '[]'

UNIQUE(workout_plan_id, position)
```

Do not prescribe arbitrary load values in the POC when no validated previous load exists.

Use `load_kg = NULL` when the user should self-select an appropriate load.

---

## 9.13 `workout_explanations`

```text
id UUID PK
workout_plan_id UUID UNIQUE NOT NULL
provider VARCHAR NOT NULL
model VARCHAR NOT NULL
short_text TEXT NOT NULL
deep_insight JSONB NULL
source_facts JSONB NOT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Store the exact structured facts passed to the LLM for traceability.

---

## 9.14 `workout_sessions`

```text
id UUID PK
user_id UUID NOT NULL
workout_plan_id UUID NOT NULL
started_at TIMESTAMPTZ NOT NULL
completed_at TIMESTAMPTZ NULL
status VARCHAR NOT NULL
completed BOOLEAN NOT NULL DEFAULT FALSE
rpe SMALLINT NULL
modifications JSONB NOT NULL DEFAULT '[]'
post_soreness_map JSONB NOT NULL DEFAULT '{}'
notes TEXT NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

Status:

```text
in_progress
completed
quit
```

RPE is `1..10`.

---

## 9.15 `weekly_summaries` — Phase 2

```text
id UUID PK
user_id UUID NOT NULL
week_start DATE NOT NULL
week_end DATE NOT NULL
consistency_score NUMERIC(5,2) NOT NULL
recovery_notes TEXT NOT NULL
progression_notes TEXT NOT NULL
planned_adjustments JSONB NOT NULL DEFAULT '{}'
metrics JSONB NOT NULL DEFAULT '{}'
deep_insight JSONB NULL
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL

UNIQUE(user_id, week_start)
```

---

# 10. Profile / Onboarding Endpoints

Implement:

```text
GET   /api/v1/me
PATCH /api/v1/me

GET   /api/v1/me/goals
PUT   /api/v1/me/goals

GET   /api/v1/me/training-profile
PUT   /api/v1/me/training-profile

GET   /api/v1/me/accessibility
PUT   /api/v1/me/accessibility

GET   /api/v1/me/equipment
PUT   /api/v1/me/equipment

GET   /api/v1/me/notifications
PUT   /api/v1/me/notifications

POST  /api/v1/me/onboarding/complete
```

## 10.1 `GET /me`

Response:

```json
{
  "id": "uuid",
  "email": "person@example.com",
  "name": "Alex",
  "age": 25,
  "height_cm": 178,
  "weight_kg": 80,
  "gender": null,
  "country": "United Kingdom",
  "onboarding_completed": false
}
```

## 10.2 `PATCH /me`

Allow partial update of:

- name,
- age,
- height,
- weight,
- gender,
- country.

Never allow client update of:

- auth_user_id,
- email identity binding,
- created_at.

---

## 10.3 `PUT /me/goals`

Request:

```json
{
  "primary_goal": "gain_muscle",
  "secondary_goal": null,
  "target_metrics": {}
}
```

---

## 10.4 `PUT /me/training-profile`

Request:

```json
{
  "experience_level": "beginner",
  "preferred_days": ["monday", "wednesday", "friday"],
  "session_length_minutes": 45
}
```

---

## 10.5 `PUT /me/accessibility`

Request:

```json
{
  "screen_reader_enabled": false,
  "high_contrast": false,
  "simple_mode": false,
  "motion_reduced": true,
  "voice_enabled": true,
  "haptics_enabled": true
}
```

Persist immediately.

---

## 10.6 `PUT /me/equipment`

Request:

```json
{
  "equipment_ids": ["uuid-1", "uuid-2"]
}
```

Replace the user's current equipment set transactionally.

---

## 10.7 `PUT /me/notifications`

Request:

```json
{
  "daily_checkin_reminders": true,
  "workout_reminders": true,
  "weekly_summary_alerts": true
}
```

---

## 10.8 `POST /me/onboarding/complete`

Before setting `onboarding_completed = true`, validate that required onboarding components exist:

- profile basics,
- primary goal,
- training profile,
- accessibility profile,
- baseline check-in.

Return a structured missing-fields error if incomplete.

---

# 11. Catalog Endpoints

Implement:

```text
GET /api/v1/catalog/equipment
GET /api/v1/catalog/exercises
GET /api/v1/catalog/exercises/{exercise_id}
```

## Equipment response

```json
{
  "items": [
    {
      "id": "uuid",
      "slug": "dumbbells",
      "name": "Dumbbells",
      "category": "dumbbell"
    }
  ]
}
```

## Exercise filters

Support optional query filters:

```text
?workout_type=strength
?equipment_id=<uuid>
?difficulty=beginner
```

The frontend should not need the full catalog for ordinary workout generation, but these endpoints support onboarding and debugging.

---

# 12. Daily Check-In Endpoints

Implement:

```text
POST /api/v1/check-ins
GET  /api/v1/check-ins/today
GET  /api/v1/check-ins/{check_in_id}
GET  /api/v1/check-ins
PUT  /api/v1/check-ins/{check_in_id}
```

## Create request

```json
{
  "energy_score": 6,
  "soreness_map": {
    "quads": 6,
    "hamstrings": 5
  },
  "mood_score": 8,
  "sleep_score": 7,
  "stress_score": 4,
  "time_available_minutes": 45,
  "pain_score": null
}
```

Rules:

- one check-in per user per calendar day,
- repeated `POST` on same day returns `409 CHECKIN_ALREADY_EXISTS`,
- use `PUT` to edit today's check-in,
- baseline onboarding check-in may omit `time_available_minutes`,
- normal daily check-in should include time available.

---

# 13. Workout Generation API

The primary endpoint:

```text
POST /api/v1/workouts/generate
```

Request:

```json
{
  "check_in_id": "uuid"
}
```

The client does not send profile/history directly.

The server loads:

- authenticated user,
- goal profile,
- training profile,
- equipment,
- check-in,
- recent workout history,
- recent session feedback.

If a workout already exists for the same check-in, return the existing plan instead of silently creating a duplicate.

Response:

```json
{
  "id": "uuid",
  "plan_date": "2026-09-08",
  "type": "strength",
  "intensity": "moderate",
  "duration_minutes": 45,
  "goal_tags": ["gain_muscle", "upper_body"],
  "short_explanation": "Your energy is moderate and your legs are still recovering, so today's session focuses more on upper-body work.",
  "exercises": [
    {
      "id": "uuid",
      "exercise_id": "uuid",
      "name": "Dumbbell Bench Press",
      "position": 1,
      "sets": 3,
      "reps_min": 8,
      "reps_max": 12,
      "load_kg": null,
      "rest_seconds": 90,
      "notes": null
    }
  ]
}
```

Other endpoints:

```text
GET /api/v1/workouts/today
GET /api/v1/workouts
GET /api/v1/workouts/{workout_id}
GET /api/v1/workouts/{workout_id}/explanation
GET /api/v1/workouts/{workout_id}/insight
```

`/insight` is Phase 2 and may return `501` or a feature-disabled response until implemented.

---

# 14. Deterministic Adaptation Engine

This section is an **implementation decision added to operationalize the product specification**. Keep all constants configurable in a single rules/config module.

The engine must return two things:

1. the plan constraints,
2. a `rule_trace` explaining exactly why those constraints were selected.

Example:

```json
{
  "recovery_score": 6.4,
  "intensity_selected": "moderate",
  "excluded_regions": ["quads"],
  "deprioritized_regions": ["hamstrings"],
  "time_limit_minutes": 45,
  "goal": "gain_muscle",
  "decision_facts": [
    "Energy score was 6/10",
    "Sleep score was 7/10",
    "Quad soreness was 8/10",
    "Available time was 45 minutes"
  ]
}
```

The explanation engine must use this trace.

---

## 14.1 Recovery score

Implement a deterministic normalized recovery score.

Initial MVP formula:

```text
energy_component = energy_score
sleep_component = sleep_score
mood_component = mood_score
stress_component = 11 - stress_score
pain_component = 10 if pain is null else (11 - pain_score)

recovery_score =
    0.30 * energy_component +
    0.25 * sleep_component +
    0.15 * mood_component +
    0.20 * stress_component +
    0.10 * pain_component
```

Round to 1 decimal.

This is a POC heuristic, not a medical score.

---

## 14.2 Intensity selection

Initial rule:

```text
recovery < 4.5       -> low
4.5 <= recovery < 7 -> moderate
recovery >= 7        -> high
```

Additional caps:

- pain >= 6 => maximum intensity `low`,
- any major region soreness >= 8 => do not heavily load that region,
- if sleep <= 3 => maximum intensity `low`,
- if stress >= 9 => maximum intensity `low`.

Keep thresholds in configuration, not scattered through code.

---

## 14.3 Soreness logic

Initial MVP:

```text
1-3 -> normal
4-6 -> deprioritize
7-10 -> exclude exercises whose primary muscle groups strongly load that region
```

Map body regions to muscle groups in one explicit configuration object.

Example:

```python
BODY_REGION_TO_MUSCLES = {
    "quads": ["quadriceps"],
    "hamstrings": ["hamstrings"],
    "glutes": ["glutes"],
    "chest": ["chest"],
    "shoulders": ["front_delts", "side_delts", "rear_delts"],
    "upper_back": ["lats", "traps", "rhomboids"],
    "lower_back": ["erectors"],
    "calves": ["calves"],
}
```

Do not use the LLM for this mapping.

---

## 14.4 Goal mapping

Initial templates:

### Lose fat

Prefer:

- mixed sessions,
- resistance + low/moderate cardio,
- full-body patterns when recovery permits.

Typical strength reps:

```text
8-15
```

### Gain muscle

Prefer:

- strength/hypertrophy,
- balanced movement patterns,
- moderate volume.

Typical reps:

```text
8-12
```

### Get stronger

Prefer:

- strength,
- lower rep ranges,
- longer rest.

Typical reps:

```text
4-8
```

For beginners, avoid aggressive prescriptions.

### Improve mobility

Prefer:

- mobility,
- controlled bodyweight,
- low intensity.

Use timed movements where appropriate instead of load.

---

## 14.5 Experience level

Use experience to bound complexity and volume.

Initial rules:

### Beginner

- 4-6 exercises for 45 minutes,
- mainly stable/simple movement patterns,
- 2-3 working sets,
- avoid unnecessary complexity.

### Intermediate

- 5-7 exercises,
- 3-4 working sets.

### Advanced

- 5-8 exercises,
- 3-5 working sets.

The duration fitter may reduce these counts.

---

## 14.6 Duration fitting

Available time is a hard upper bound.

Estimate exercise time from:

```text
sets * estimated_set_time
+
rest intervals
+
small transition allowance
```

Use conservative estimates.

The plan builder must trim exercises until estimated total duration fits within:

```text
time_available_minutes
```

If the normal daily check-in omits time available, fall back to the user's training profile session length.

---

## 14.7 Equipment filter

Only choose an exercise if:

- it requires no equipment, or
- the user owns all required equipment.

No hallucinated equipment.

---

## 14.8 Movement balance

For normal strength/mixed sessions, when not prevented by soreness:

Try to avoid plans containing only one movement pattern.

Prefer reasonable balance among:

- lower-body knee dominant,
- lower-body hinge,
- push,
- pull,
- core,
- optional conditioning.

Do not force a sore/excluded pattern merely to achieve balance.

---

## 14.9 Recent history

Use recent workout history to avoid repeatedly choosing the same exact exercise unnecessarily.

Initial POC:

- inspect the last 3 completed sessions,
- slightly de-prioritize exercises used in the immediately previous session,
- do not exclude them absolutely,
- prefer alternative exercises with the same movement pattern when available.

---

## 14.10 Load prescription

POC rule:

- if there is no trustworthy previous load history, return `load_kg = null`,
- do not invent weight based solely on body weight,
- if a future phase records actual working loads, progression may use that history.

This keeps the POC conservative.

---

## 14.11 Safety behavior

This application is a general fitness POC, not a medical diagnostic system.

Hard requirements:

- do not diagnose injuries,
- do not claim medical certainty,
- do not tell a user to train through severe pain,
- if pain/soreness makes safe generation impossible under configured rules, return a controlled response rather than forcing a plan.

Example controlled error:

```json
{
  "error": {
    "code": "WORKOUT_GENERATION_RESTRICTED",
    "message": "Today's check-in contains recovery or pain values that prevent the normal workout generator from producing a suitable session.",
    "details": {
      "suggested_action": "review_checkin"
    }
  }
}
```

Do not use an LLM to override a deterministic restriction.

---

# 15. Workout Plan Validator

Create a validator service that runs before persistence.

It must verify:

- all exercise ids exist,
- all exercises are active,
- equipment requirements are satisfied,
- excluded soreness regions are respected,
- duration is within allowed limit,
- intensity is valid,
- sets/reps/durations are positive,
- exercise positions are unique,
- no duplicate plan rows,
- no arbitrary unknown enum values.

If validation fails because the deterministic builder made a bad selection:

1. retry once with a simplified fallback selection,
2. if still invalid, return a controlled error.

Never persist a known-invalid plan.

---

# 16. AI Explanation Engine

The LLM is for language generation, not planning.

## 16.1 Provider interface

Create:

```python
class AIProvider(Protocol):
    async def generate_short_explanation(
        self,
        source_facts: dict,
        workout_plan: dict,
    ) -> str:
        ...

    async def generate_deep_insight(
        self,
        source_facts: dict,
        workout_plan: dict,
        history_summary: dict,
    ) -> dict:
        ...
```

Implement:

```text
GeminiAIProvider
MockAIProvider
```

Provider is selected from configuration.

---

## 16.2 Short explanation constraints

Prompt must instruct the model:

- use only supplied facts,
- never invent measurements,
- never invent medical claims,
- never introduce new exercises,
- never claim the user has a condition,
- keep to one sentence,
- use warm coach tone,
- be transparent about the main adaptation reason.

Example facts:

```json
{
  "energy_score": 6,
  "sleep_score": 7,
  "stress_score": 4,
  "high_soreness_regions": ["quads"],
  "time_available_minutes": 45,
  "selected_intensity": "moderate",
  "selected_focus": "upper_body"
}
```

Expected style:

```text
"Your energy is moderate and your quads are still recovering, so today's 45-minute session keeps the intensity balanced and shifts more work to your upper body."
```

---

## 16.3 Fallback explanation

If:

- provider times out,
- API key missing,
- quota exhausted,
- output fails validation,

build a deterministic template from `rule_trace`.

The workout generation endpoint must still succeed.

Example:

```text
"Today's plan uses moderate intensity based on your check-in and keeps work away from highly sore areas."
```

---

## 16.4 Output validation

Reject/regenerate/fallback if LLM output:

- contains unsupported numeric facts,
- mentions an exercise not in the plan,
- is empty,
- is too long,
- contains diagnostic medical language.

For the POC, use conservative string/fact checks rather than another LLM judge.

---

# 17. Deep Insight — Phase 2

Endpoint:

```text
GET /api/v1/workouts/{workout_id}/insight
```

Response:

```json
{
  "sections": [
    {
      "type": "recovery",
      "title": "Recovery Insight",
      "content": "..."
    },
    {
      "type": "energy",
      "title": "Energy Trend",
      "content": "..."
    },
    {
      "type": "soreness",
      "title": "Soreness Analysis",
      "content": "..."
    },
    {
      "type": "burnout",
      "title": "Burnout Risk",
      "content": "..."
    },
    {
      "type": "progression",
      "title": "Long-Term Progression Impact",
      "content": "..."
    }
  ]
}
```

Generate only from stored structured facts and history summaries.

Persist result so repeatedly opening the panel does not repeatedly call the LLM.

---

# 18. Workout Session Endpoints

Implement:

```text
POST /api/v1/workout-sessions
GET  /api/v1/workout-sessions/{session_id}
POST /api/v1/workout-sessions/{session_id}/complete
POST /api/v1/workout-sessions/{session_id}/quit
```

## 18.1 Start session

Request:

```json
{
  "workout_id": "uuid"
}
```

Response:

```json
{
  "id": "uuid",
  "workout_id": "uuid",
  "status": "in_progress",
  "started_at": "2026-09-08T14:00:00Z"
}
```

Starting a workout should update plan status to `started`.

Prevent users from starting another user's workout.

---

## 18.2 Complete session

Request:

```json
{
  "rpe": 7,
  "modifications": [
    "reduced_load"
  ],
  "post_soreness_map": {
    "shoulders": 3
  },
  "notes": "Last set was difficult."
}
```

On success:

- session status -> completed,
- completed -> true,
- completed_at -> now,
- workout plan status -> completed.

Return updated session plus daily summary.

---

## 18.3 Quit session

Request may include optional reason/notes.

Set:

```text
status = quit
completed = false
```

Do not delete the session.

---

# 19. Home Dashboard Endpoint

Implement aggregation endpoint:

```text
GET /api/v1/home
```

Response:

```json
{
  "date": "2026-09-08",
  "check_in_completed": true,
  "today_workout": {
    "id": "uuid",
    "type": "strength",
    "intensity": "moderate",
    "duration_minutes": 45,
    "status": "generated",
    "short_explanation": "..."
  },
  "consistency_score": 72.0,
  "current_streak": 4,
  "quick_stats": {
    "completed_sessions_7d": 3
  }
}
```

This endpoint exists to reduce frontend request fan-out.

---

# 20. Progress Endpoints

Implement:

```text
GET /api/v1/progress
GET /api/v1/progress/workouts
GET /api/v1/progress/check-ins
```

## 20.1 `GET /progress`

Initial response:

```json
{
  "consistency_score": 68.0,
  "current_streak": 3,
  "completed_sessions_7d": 3,
  "planned_sessions_7d": 4,
  "energy_trend": {
    "direction": "up",
    "change_percent": 5.0
  },
  "recovery_trend": {
    "direction": "stable",
    "change_percent": 1.0
  },
  "strength_progression": {
    "direction": "insufficient_data",
    "change_percent": null
  }
}
```

Do not fabricate trends when there is insufficient data.

---

## 20.2 Consistency score

Initial POC formula:

```text
completed planned sessions / planned sessions * 100
```

For users with no planned sessions:

```text
consistency_score = 0
```

Document the denominator.

Use preferred training days to infer planned sessions for the period.

---

## 20.3 Current streak

Count consecutive planned workout days completed.

Do not count non-planned rest days as broken streaks.

---

# 21. Weekly Engine — Phase 2

Implement:

```text
GET  /api/v1/weekly/current
GET  /api/v1/weekly/{week_start}
POST /api/v1/weekly/generate
GET  /api/v1/weekly/{week_start}/insight
```

## 21.1 Weekly generation

Aggregate:

- planned sessions,
- completed sessions,
- RPE,
- check-in recovery scores,
- energy trend,
- soreness trend,
- workout intensity mix.

Produce:

```json
{
  "consistency_score": 75,
  "recovery_notes": "...",
  "progression_notes": "...",
  "planned_adjustments": {
    "volume_direction": "maintain",
    "intensity_cap": null,
    "focus_notes": []
  }
}
```

Use deterministic aggregation first.

LLM may turn facts into readable notes but may not invent metrics.

---

# 22. Seed Data

Create deterministic seed files.

## 22.1 Equipment seed

Include at minimum:

```text
Bodyweight
Dumbbells
Barbell
Bench
Squat Rack
Cable Machine
Resistance Bands
Kettlebell
Pull-up Bar
Treadmill
Exercise Bike
Rowing Machine
Yoga Mat
```

Use stable slugs.

---

## 22.2 Exercise seed

Create at least 40 common exercises across:

- bodyweight,
- dumbbell,
- barbell,
- cable/machine,
- cardio,
- mobility.

Each exercise must have:

- stable slug,
- name,
- workout type,
- movement pattern,
- primary muscles,
- secondary muscles,
- difficulty,
- equipment requirements,
- default rest.

Examples:

```text
bodyweight_squat
goblet_squat
barbell_back_squat
romanian_deadlift
dumbbell_bench_press
push_up
overhead_press
seated_cable_row
one_arm_dumbbell_row
lat_pulldown
assisted_pull_up
plank
dead_bug
walking
treadmill_walk
stationary_bike
hip_flexor_stretch
thoracic_rotation
cat_cow
```

Avoid obscure/highly technical choices in the default beginner catalog.

Seeding must be idempotent.

---

# 23. Frontend Collaboration / Staging Requirements

The frontend developer is remote and must be able to use the API over the internet.

## 23.1 Public staging URL

Deploy the API to a public host.

Expected form:

```text
https://<staging-api-host>/api/v1
```

Expose:

```text
/docs
/openapi.json
/api/v1/health
```

in staging.

## 23.2 CORS

Read allowed origins from configuration:

```env
FRONTEND_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8081,https://frontend-staging.example
```

Do not permanently use unrestricted `*` in production.

For native mobile clients CORS may not apply the same way as browsers, but keep web support correct.

## 23.3 Frontend environment example

```env
VITE_API_URL=https://<staging-api-host>/api/v1
```

or:

```env
EXPO_PUBLIC_API_URL=https://<staging-api-host>/api/v1
```

## 23.4 Test users

Provide a script:

```bash
python scripts/create_test_user.py
```

If automated user creation requires a service-role key, keep that script server-side only.

Never share the service-role key with the frontend developer.

---

# 24. Implementation Phases

Codex must build in this order.

---

## Phase 0 — Bootstrap

Deliver:

- project structure,
- FastAPI app,
- config,
- `/health`,
- `/version`,
- logging,
- error handler,
- CORS,
- pyproject,
- Dockerfile,
- docker-compose,
- README,
- test harness.

Acceptance:

```bash
pytest
```

passes.

```bash
uvicorn app.main:app --reload
```

starts.

`GET /api/v1/health` returns 200.

---

## Phase 1 — Database + migrations

Deliver:

- SQLAlchemy async database layer,
- all Phase 1 models,
- Alembic,
- first migration,
- local Postgres Docker service.

Acceptance:

- migration upgrades empty DB,
- migration downgrade is valid where practical,
- app starts with DB connection.

---

## Phase 2 — Auth

Deliver:

- signup,
- login,
- refresh,
- forgot password,
- logout,
- `get_current_user`,
- protected endpoint tests,
- mock auth mode for tests.

Acceptance:

- invalid token -> 401,
- user cannot access another user's resources.

---

## Phase 3 — Onboarding/Profile

Deliver all `/me/*` endpoints.

Acceptance:

- complete onboarding flow can be persisted,
- equipment update is transactional,
- accessibility toggle updates immediately,
- onboarding complete rejects missing required state.

---

## Phase 4 — Catalog

Deliver:

- seed data,
- equipment endpoint,
- exercise endpoint,
- exercise filters.

Acceptance:

- seed is idempotent,
- workout engine can query valid candidate exercises.

---

## Phase 5 — Check-Ins

Deliver all check-in endpoints.

Acceptance:

- scores validated,
- one per user/day,
- today retrieval works,
- user isolation works.

---

## Phase 6 — Deterministic Workout Engine

Deliver:

- recovery rules,
- soreness rules,
- intensity rules,
- equipment filtering,
- duration fitter,
- goal logic,
- experience logic,
- recent-history de-prioritization,
- plan validation,
- `POST /workouts/generate`,
- workout retrieval endpoints.

Acceptance:

- same inputs + same seed + same history produce deterministic plan,
- high soreness excludes affected primary-muscle exercises,
- plan fits time,
- unavailable equipment is never selected,
- workout cannot include unknown exercises,
- duplicate retries return existing plan.

---

## Phase 7 — AI Explanation

Deliver:

- provider protocol,
- Gemini adapter,
- mock adapter,
- prompt,
- output validator,
- deterministic fallback,
- explanation persistence.

Acceptance:

- workout generation succeeds if AI fails,
- explanation does not contain unsupported exercises,
- short explanation is one sentence,
- repeated reads do not repeatedly call provider.

---

## Phase 8 — Workout Sessions

Deliver:

- start,
- complete,
- quit,
- session ownership checks,
- status transitions.

Acceptance:

- completing session updates plan,
- invalid RPE rejected,
- another user cannot modify session.

---

## Phase 9 — Home + Progress

Deliver:

- home aggregate,
- consistency score,
- streak,
- history lists,
- basic trend calculations.

Acceptance:

- no-data users receive valid empty state values,
- insufficient data is not fabricated.

---

## Phase 10 — Phase 2 Weekly + Deep Insight

Deliver:

- weekly summaries,
- planned adjustments,
- workout Deep Insight,
- weekly Deep Insight,
- persistence/caching.

Acceptance:

- facts trace back to stored user metrics,
- repeated reads use persisted result.

---

## Phase 11 — Deployment

Deliver:

- production-ready Docker build,
- staging deployment instructions,
- environment variable documentation,
- public staging URL,
- migrations applied,
- Swagger reachable,
- health check configured.

The initial deployment target may be Koyeb, Render, or an equivalent low-cost/free POC host. Keep the container portable.

---

# 25. Testing Strategy

Tests are mandatory.

## 25.1 Unit tests

Test pure business logic:

```text
recovery score
intensity selection
soreness exclusions
equipment filtering
duration fitting
goal mapping
experience volume
history de-prioritization
consistency
streak
LLM output validator
```

The deterministic rules must be testable without database or internet.

---

## 25.2 Integration tests

Test:

- DB repositories,
- protected API routes,
- auth dependency,
- ownership,
- generation persistence,
- session transitions,
- progress aggregation.

Use isolated test database.

---

## 25.3 Critical scenario tests

### Scenario A — normal workout

```text
Goal: gain muscle
Experience: beginner
Equipment: dumbbells + bench
Energy: 7
Sleep: 7
Stress: 4
Low soreness
Time: 45
```

Expected:

- moderate/high allowed according to recovery,
- only available equipment,
- duration <= 45.

### Scenario B — sore quads

```text
Quad soreness: 9
```

Expected:

- no exercise primarily loading quads.

### Scenario C — low recovery

```text
Energy: 3
Sleep: 2
Stress: 9
```

Expected:

- intensity low.

### Scenario D — no equipment

Expected:

- bodyweight/mobility/cardio options only.

### Scenario E — 15 minutes

Expected:

- short valid workout <= 15 minutes.

### Scenario F — AI offline

Expected:

- plan generation still succeeds,
- deterministic explanation fallback returned.

### Scenario G — ownership

User B requests User A's workout id.

Expected:

```text
404 or 403
```

Choose one policy and use it consistently; prefer 404 to avoid resource enumeration.

---

# 26. API Contract Summary

Final planned route list:

```text
/api/v1

AUTH
POST   /auth/signup
POST   /auth/login
POST   /auth/refresh
POST   /auth/forgot-password
POST   /auth/logout

ME
GET    /me
PATCH  /me
GET    /me/goals
PUT    /me/goals
GET    /me/training-profile
PUT    /me/training-profile
GET    /me/accessibility
PUT    /me/accessibility
GET    /me/equipment
PUT    /me/equipment
GET    /me/notifications
PUT    /me/notifications
POST   /me/onboarding/complete

CATALOG
GET    /catalog/equipment
GET    /catalog/exercises
GET    /catalog/exercises/{exercise_id}

CHECK-INS
POST   /check-ins
GET    /check-ins/today
GET    /check-ins
GET    /check-ins/{check_in_id}
PUT    /check-ins/{check_in_id}

WORKOUTS
POST   /workouts/generate
GET    /workouts/today
GET    /workouts
GET    /workouts/{workout_id}
GET    /workouts/{workout_id}/explanation
GET    /workouts/{workout_id}/insight

SESSIONS
POST   /workout-sessions
GET    /workout-sessions/{session_id}
POST   /workout-sessions/{session_id}/complete
POST   /workout-sessions/{session_id}/quit

HOME / PROGRESS
GET    /home
GET    /progress
GET    /progress/workouts
GET    /progress/check-ins

WEEKLY
GET    /weekly/current
GET    /weekly/{week_start}
POST   /weekly/generate
GET    /weekly/{week_start}/insight

SYSTEM
GET    /health
GET    /version
```

---

# 27. OpenAPI Requirements

FastAPI generated docs must include:

- endpoint summary,
- endpoint description,
- auth indicator,
- request examples,
- response examples,
- documented error codes.

Use tags:

```text
Auth
Profile
Catalog
Check-Ins
Workouts
Sessions
Progress
Weekly
System
```

Set a clear API title and version.

---

# 28. Logging

Use structured logging.

Log:

- request id,
- method,
- path,
- status,
- duration,
- user id when authenticated,
- workout generation version,
- AI provider latency/failure category.

Never log:

- password,
- refresh token,
- full access token,
- service-role key,
- raw secrets.

For AI calls, avoid logging unnecessarily sensitive free-text user notes.

---

# 29. Request IDs

Add middleware generating/requesting:

```text
X-Request-ID
```

Return it in responses.

Include it in error logs.

---

# 30. Basic Rate Limiting

Do not over-engineer.

At minimum protect expensive generation routes conceptually:

```text
POST /workouts/generate
GET /workouts/{id}/insight
POST /weekly/generate
```

For the POC, if no Redis is used, implement a simple per-process limiter only if needed, or rely on platform/API-provider limits.

Do not add Redis solely for this requirement.

Document the limitation.

---

# 31. Database Transactions

Use transactions for operations that must remain consistent.

Examples:

- equipment replacement,
- workout plan + workout exercises persistence,
- session completion + plan status update,
- weekly summary write.

Never leave a workout plan persisted without its exercise rows because of a partial failure.

---

# 32. Concurrency / Idempotency

Workout generation must handle frontend retries.

Use a DB uniqueness rule or transaction lock around:

```text
(user_id, check_in_id)
```

If two requests arrive concurrently, only one plan becomes the canonical generated plan.

The other request should return the existing plan.

---

# 33. Security Requirements

1. Passwords handled only by Supabase Auth.
2. All personal-resource endpoints require authentication.
3. Never trust client-provided ownership ids.
4. Use parameterized ORM queries.
5. Validate all input through Pydantic.
6. Restrict CORS in staging/production.
7. Keep secrets in environment variables.
8. Do not expose service-role key.
9. Disable or protect docs in true production if required.
10. Do not reveal stack traces to clients.
11. Apply ownership filters at repository/service boundaries.
12. Limit free-text notes length.
13. Limit JSON body sizes reasonably.

---

# 34. Accessibility Backend Responsibilities

Most accessibility behavior is frontend-rendering behavior, but backend must:

- persist six accessibility toggles,
- return them quickly with profile state,
- preserve values across devices,
- never use accessibility preference to deny core backend functionality,
- support simple-mode/front-end decisions through the stored profile.

The backend does not render WCAG behavior itself.

---

# 35. Performance Targets

Product target for workout generation is under approximately 3 seconds where practical.

Engineering approach:

- deterministic generation should normally finish in milliseconds,
- persist the plan before optional slow AI explanation if architecture requires,
- use low-latency AI call,
- timeout AI call,
- fall back instead of blocking indefinitely,
- avoid N+1 queries,
- preload catalog relationships efficiently.

Target API response times for ordinary DB endpoints:

```text
< 500 ms in normal staging conditions
```

Do not treat this as a hard SLA for a sleeping free host.

---

# 36. AI Timeout / Failure Policy

Configure:

```text
AI_TIMEOUT_SECONDS
```

Suggested starting value:

```text
2.0 to 3.0 seconds
```

If AI exceeds timeout:

- log provider timeout,
- use deterministic explanation,
- do not fail the workout.

For Deep Insight, a provider failure may return:

```text
503 AI_INSIGHT_UNAVAILABLE
```

because Deep Insight itself is optional.

---

# 37. Versioning

API prefix remains:

```text
/api/v1
```

Workout generator has its own version:

```text
generator_version = "rules-v1"
```

Persist it with each workout.

When rules change materially later:

```text
rules-v2
```

This supports reproducibility and debugging.

---

# 38. README Requirements

README must include:

1. project description,
2. architecture summary,
3. prerequisites,
4. local setup,
5. environment variables,
6. database migration commands,
7. seed commands,
8. run commands,
9. tests,
10. Swagger URL,
11. Docker commands,
12. staging deployment notes,
13. frontend integration example.

Example local flow:

```bash
cp .env.example .env
docker compose up -d db
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 39. Docker

Dockerfile must:

- use a slim Python base,
- install dependencies,
- run as non-root where practical,
- expose port,
- start Uvicorn using environment-provided port if host requires it.

Do not bake secrets into the image.

`docker-compose.yml` should support:

- API,
- PostgreSQL,

for local development.

---

# 40. CI

Create GitHub Actions workflow.

On pull request and push:

1. install dependencies,
2. run Ruff,
3. run tests,
4. optionally run type checking,
5. verify migrations/imports.

Do not deploy on every branch unless explicitly configured.

---

# 41. Coding Style

- type hints on public/service functions,
- async database access,
- small routers,
- services own business logic,
- repositories own queries,
- no SQL in routers,
- no AI calls in routers,
- no hard-coded secrets,
- avoid giant utility modules,
- prefer enums/constants for repeated domain values,
- descriptive names,
- docstrings for non-obvious rules.

---

# 42. Pydantic Validation Examples

Scores:

```python
Field(ge=1, le=10)
```

Notes:

```python
Field(max_length=2000)
```

Name:

```python
Field(min_length=1, max_length=120)
```

Session lengths:

validate enum/set:

```text
15, 30, 45, 60
```

Preferred days:

only:

```text
monday
tuesday
wednesday
thursday
friday
saturday
sunday
```

---

# 43. Data Ownership Pattern

Every repository lookup of a protected entity should include current user.

Preferred:

```python
get_workout(workout_id, user_id)
```

Not:

```python
get_workout(workout_id)
```

followed by a late ownership check.

This reduces accidental information disclosure.

---

# 44. No-Data Behavior

Endpoints must return useful empty states rather than errors where absence is normal.

Examples:

### No workout today

```json
{
  "today_workout": null
}
```

### No progress

```json
{
  "consistency_score": 0,
  "current_streak": 0,
  "completed_sessions_7d": 0
}
```

### No weekly summary

Return `404 WEEKLY_SUMMARY_NOT_FOUND` when directly requesting a specific week, but home/progress should tolerate absence.

---

# 45. Date / Time Handling

- store timestamps in UTC,
- determine `checkin_date` and `plan_date` using an explicit user timezone when eventually added,
- for the POC, add optional `timezone` to profile if needed or use a configured default,
- never use server-local timezone implicitly.

If timezone is added, use IANA names:

```text
Europe/London
America/Toronto
Africa/Harare
```

This is an implementation improvement not explicitly present in the original product brief.

---

# 46. Recommended Additional Profile Field

Add:

```text
timezone VARCHAR NULL
```

to `profiles`.

Reason:

daily check-ins, "today", streaks, and weekly summaries require a stable notion of the user's local date.

If omitted, default behavior must be clearly documented.

---

# 47. Frontend API Handoff

Create `docs/frontend-api.md`.

It must contain:

- base URL,
- auth flow,
- how to pass Bearer token,
- all endpoint paths,
- key request/response examples,
- error envelope,
- CORS note,
- staging Swagger URL.

The frontend developer should be able to integrate without reading backend implementation code.

---

# 48. Suggested Initial API Usage Flow

```text
POST /auth/signup
        |
        v
PATCH /me
        |
        v
PUT /me/goals
        |
        v
PUT /me/training-profile
        |
        v
PUT /me/equipment
        |
        v
PUT /me/accessibility
        |
        v
POST /check-ins
        |
        v
POST /me/onboarding/complete
        |
        v
POST /workouts/generate
        |
        v
GET /workouts/{id}
        |
        v
POST /workout-sessions
        |
        v
POST /workout-sessions/{id}/complete
        |
        v
GET /home
        |
        v
GET /progress
```

For later daily use:

```text
GET /home
   |
   +-- no today's check-in --> POST /check-ins
                               |
                               v
                        POST /workouts/generate
                               |
                               v
                        start/complete session
```

---

# 49. Phase 1 Definition of Done

Phase 1 is complete only when all of the following are true:

- [ ] app starts locally,
- [ ] database migrations run,
- [ ] seed data loads,
- [ ] signup works,
- [ ] login works,
- [ ] protected routes reject invalid tokens,
- [ ] profile persists,
- [ ] goal persists,
- [ ] training profile persists,
- [ ] accessibility persists,
- [ ] equipment persists,
- [ ] check-in persists,
- [ ] deterministic workout generates,
- [ ] workout uses only available equipment,
- [ ] soreness adaptation works,
- [ ] duration adaptation works,
- [ ] generated plan is validated,
- [ ] short explanation exists,
- [ ] AI failure falls back,
- [ ] workout can be started,
- [ ] workout can be completed,
- [ ] feedback persists,
- [ ] home endpoint works,
- [ ] progress endpoint works,
- [ ] tests pass,
- [ ] Swagger works,
- [ ] Docker works,
- [ ] staging deployment is reachable by the frontend developer.

---

# 50. Final Codex Execution Instruction

Begin at **Phase 0**.

Do not try to generate the entire codebase in one uncontrolled pass.

For each phase:

1. inspect existing files,
2. state the phase being implemented,
3. create/update the necessary files,
4. run formatting/linting,
5. run relevant tests,
6. fix failures,
7. update README if setup changed,
8. update CHANGELOG,
9. summarize what is complete,
10. proceed to the next phase unless genuinely blocked.

When choosing between a complex and simple implementation that both satisfy the specification, choose the simpler implementation.

Do not defer core Phase 1 functionality with TODO placeholders.

The final deliverable is a running backend, not merely scaffolding.

---

# Appendix A — Core Domain Enums

```text
PrimaryGoal:
- lose_fat
- gain_muscle
- get_stronger
- improve_mobility

ExperienceLevel:
- beginner
- intermediate
- advanced

WorkoutType:
- strength
- cardio
- mobility
- mixed

Intensity:
- low
- moderate
- high

WorkoutStatus:
- generated
- started
- completed
- cancelled

SessionStatus:
- in_progress
- completed
- quit
```

---

# Appendix B — Canonical Body Regions

Use these keys consistently in API payloads:

```text
chest
shoulders
upper_back
lower_back
biceps
triceps
forearms
core
glutes
quads
hamstrings
calves
hips
knees
ankles
```

Not every region needs to map directly to a muscle group. Joint regions such as knees/ankles should conservatively affect related lower-body exercise selection.

Keep the mapping explicit and testable.

---

# Appendix C — Canonical Error Codes

Start with:

```text
AUTH_REQUIRED
AUTH_INVALID
AUTH_EXPIRED

PROFILE_NOT_FOUND
ONBOARDING_INCOMPLETE

CHECKIN_NOT_FOUND
CHECKIN_ALREADY_EXISTS
CHECKIN_INVALID

WORKOUT_NOT_FOUND
WORKOUT_ALREADY_EXISTS
WORKOUT_GENERATION_FAILED
WORKOUT_GENERATION_RESTRICTED
WORKOUT_VALIDATION_FAILED

SESSION_NOT_FOUND
SESSION_ALREADY_COMPLETED
SESSION_INVALID_STATE

EXERCISE_NOT_FOUND
EQUIPMENT_NOT_FOUND

AI_EXPLANATION_UNAVAILABLE
AI_INSIGHT_UNAVAILABLE

WEEKLY_SUMMARY_NOT_FOUND

VALIDATION_ERROR
RATE_LIMITED
INTERNAL_ERROR
DEPENDENCY_UNAVAILABLE
```

Use one centralized error code definition.

---

# Appendix D — Example `rule_trace`

```json
{
  "version": "rules-v1",
  "recovery": {
    "score": 6.4,
    "energy": 6,
    "sleep": 7,
    "mood": 8,
    "stress": 4,
    "pain": null
  },
  "soreness": {
    "excluded_regions": ["quads"],
    "deprioritized_regions": ["hamstrings"]
  },
  "constraints": {
    "time_available_minutes": 45,
    "equipment_slugs": ["bodyweight", "dumbbells", "bench"],
    "experience_level": "beginner",
    "primary_goal": "gain_muscle"
  },
  "decisions": {
    "intensity": "moderate",
    "workout_type": "strength",
    "focus": ["upper_body", "core"]
  },
  "decision_facts": [
    "Recovery score was 6.4/10.",
    "Quad soreness was high.",
    "Hamstring soreness was moderate.",
    "Available time was 45 minutes.",
    "Primary goal was gain muscle."
  ]
}
```

This object is the canonical truth used for explanations.

---

# Appendix E — Minimal Deployment Checklist

Before giving the staging URL to the frontend developer:

- [ ] staging database exists,
- [ ] migrations applied,
- [ ] catalog seeded,
- [ ] auth configured,
- [ ] CORS contains frontend local origin,
- [ ] AI key configured or fallback enabled,
- [ ] `/api/v1/health` returns 200,
- [ ] `/docs` opens,
- [ ] test signup/login works,
- [ ] test check-in works,
- [ ] test workout generation works,
- [ ] no secret appears in logs,
- [ ] environment is clearly marked staging.

---

# Appendix F — Important Product Boundaries

The backend should preserve these product principles:

1. The app is adaptive, but decisions must remain explainable.
2. Accessibility is foundational, not a later retrofit.
3. Daily adaptation belongs in Phase 1.
4. Weekly macro-learning belongs in Phase 2.
5. The default user experience gets a short explanation.
6. Deep Insight is optional/on-demand.
7. The system must degrade gracefully when AI is unavailable.
8. Workout generation must be deterministic and testable enough to debug.
9. The product should not present invented metrics as real measurements.
10. Clarity and reliability matter more than architectural complexity for the POC.
