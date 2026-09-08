# Frontend API Handoff

Everything a frontend developer needs to integrate with the Adaptive Fitness
Coach backend without reading backend code.

## Base URL

```text
Staging: https://<staging-api-host>/api/v1
Local:   http://localhost:8000/api/v1
```

Swagger UI (staging): `https://<staging-api-host>/docs`
OpenAPI spec: `https://<staging-api-host>/openapi.json`

## Auth flow

1. `POST /auth/signup` with `{"email", "password"}` (min 8 chars).
   - 200: `{access_token, refresh_token, expires_in, token_type, user{id,email}}`
   - 200 alt: `{"requires_email_confirmation": true}` — ask the user to check
     their inbox before login.
2. `POST /auth/login` — same token response as signup.
3. `POST /auth/refresh` with `{"refresh_token"}` — rotate tokens.
4. `POST /auth/forgot-password` with `{"email"}` — always 200.
5. `POST /auth/logout` with the Bearer token — 204.

Pass the access token on every protected request:

```http
Authorization: Bearer <access_token>
```

401 = missing/invalid/expired token (codes `AUTH_REQUIRED`, `AUTH_INVALID`,
`AUTH_EXPIRED`).

## Error envelope

All errors use the same shape:

```json
{
  "error": {
    "code": "CHECKIN_ALREADY_EXISTS",
    "message": "A check-in already exists for today. Use PUT to update it.",
    "details": {}
  }
}
```

Common codes: `VALIDATION_ERROR` (422), `ONBOARDING_INCOMPLETE` (422, with
`details.missing`), `WORKOUT_GENERATION_RESTRICTED` (422),
`RATE_LIMITED` (429), `AI_INSIGHT_UNAVAILABLE` (503),
`DEPENDENCY_UNAVAILABLE` (503).

## Suggested first-time flow

```text
POST /auth/signup
PATCH /me                       {name, age, height_cm, weight_kg, ...}
PUT  /me/goals                  {primary_goal: lose_fat|gain_muscle|get_stronger|improve_mobility}
PUT  /me/training-profile       {experience_level: beginner|intermediate|advanced,
                                 preferred_days: [monday..sunday], session_length_minutes: 15|30|45|60}
PUT  /me/equipment              {equipment_ids: [ids from GET /catalog/equipment]}
PUT  /me/accessibility          {6 boolean toggles}
POST /check-ins                 daily recovery check-in (see below)
POST /me/onboarding/complete    -> 422 ONBOARDING_INCOMPLETE until everything exists
POST /workouts/generate         {"check_in_id": ...}
GET  /workouts/{id}             full plan + exercises + short_explanation
POST /workout-sessions          {"workout_id": ...}
POST /workout-sessions/{id}/complete  {rpe 1..10, modifications[], post_soreness_map{}, notes}
GET  /home                      dashboard aggregate
```

## Daily flow

```text
GET /home
  -> check_in_completed == false -> POST /check-ins
  -> today_workout == null       -> POST /workouts/generate {"check_in_id"}
  -> start + complete a session
```

## Check-in payload

```json
{
  "energy_score": 6,          // 1..10
  "soreness_map": {"quads": 6, "hamstrings": 5},
  "mood_score": 8,            // 1..10
  "sleep_score": 7,           // 1..10
  "stress_score": 4,          // 1..10
  "time_available_minutes": 45, // optional, 5..240
  "pain_score": null          // optional, 1..10
}
```

Canonical region keys: `chest, shoulders, upper_back, lower_back, biceps,
triceps, forearms, core, glutes, quads, hamstrings, calves, hips, knees,
ankles`. One check-in per day (`409 CHECKIN_ALREADY_EXISTS`); edit today's with
`PUT /check-ins/{id}`.

## Workout generation

```text
POST /workouts/generate  {"check_in_id": "<uuid>"}
```

- The client never sends profile/history — the server loads everything.
- Deterministic: same check-in always yields the same plan; repeated calls
  return the existing plan (no duplicates).
- Soreness >= 7 in a region excludes exercises that strongly load it; pain >= 8
  returns `422 WORKOUT_GENERATION_RESTRICTED` instead of a plan.
- Response includes `short_explanation` (AI-generated from the rule trace,
  deterministic fallback if the AI is down), `exercises[]` with sets/reps or
  `duration_seconds` for timed movements, and `load_kg: null` (self-select).
- `GET /workouts/{id}/insight` returns five Deep Insight sections
  (`recovery, energy, soreness, burnout, progression`); first call generates
  and persists, may return `503 AI_INSIGHT_UNAVAILABLE` if the AI is down.

## Sessions

```text
POST /workout-sessions                       {"workout_id"}
GET  /workout-sessions/{session_id}
POST /workout-sessions/{session_id}/complete {rpe, modifications[], post_soreness_map{}, notes}
POST /workout-sessions/{session_id}/quit     {notes?}
```

Completing a session also completes the plan and returns a
`daily_summary` (`completed_sessions_today`, `consistency_score`,
`current_streak`).

## Weekly (Phase 2)

```text
GET  /weekly/current               -> 404 until generated
POST /weekly/generate              {"week_start": "2026-09-07"?}  (default: this week)
GET  /weekly/{week_start}
GET  /weekly/{week_start}/insight
```

`planned_adjustments`: `{volume_direction: up|maintain|down, intensity_cap:
null|low, focus_notes: []}`.

## Pagination

List endpoints use `?page=1&page_size=20` (max 100):

```json
{"items": [], "page": 1, "page_size": 20, "total": 0}
```

## CORS

Browser clients must have their origin registered in the backend's
`FRONTEND_ORIGINS` allow-list. Native mobile clients are unaffected but must
still send the Bearer header.

## Dates / timezone

Timestamps are ISO-8601 UTC. `checkin_date` / `plan_date` use the user's
timezone (`profiles.timezone`, IANA name, default `UTC`) — send a timezone in
`PATCH /me` if the user is not UTC.
