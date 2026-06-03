# APEX Backend — FastAPI + PostgreSQL

AI-Powered Physique & Training Analyzer — Production Backend

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT + Refresh Tokens |
| Validation | Pydantic v2 |
| Testing | Pytest + pytest-asyncio |
| Deployment | Docker + Docker Compose |

## Database ERD

```
users
  id, first_name, last_name, email, password_hash, is_active, is_superuser
  created_at, updated_at
    │
    ├──── user_profiles (1:1)
    │       id, user_id(FK), age, gender, height_cm, weight_kg
    │       fitness_goal, experience_level, bio
    │
    ├──── body_metrics (1:N — historical records)
    │       id, user_id(FK), height_cm, weight_kg, body_fat_pct
    │       chest_cm, waist_cm, shoulders_cm, arms_cm, forearms_cm
    │       neck_cm, thighs_cm, calves_cm, hips_cm, notes
    │
    ├──── training_plans (1:N)
    │       id, user_id(FK), name, description, goal
    │       experience_level, workout_split, days_per_week
    │       duration_weeks, is_active, is_ai_generated, ai_model_version
    │           │
    │           └──── training_plan_exercises (1:N)
    │                   id, plan_id(FK), exercise_id(FK)
    │                   day_of_week, order_in_session
    │                   sets, reps_min, reps_max, rest_seconds
    │                   weight_kg, notes
    │
    └──── refresh_tokens (1:N)
            id, user_id(FK), token, expires_at, is_revoked

exercises (global, not user-scoped)
  id, name, muscle_group, difficulty, equipment
  exercise_type, description, video_url, is_active
```

## Quick Start

```bash
# 1. Clone and enter directory
git clone <repo> && cd apex-backend

# 2. Create environment file
cp .env.example .env
# Edit .env — set a real SECRET_KEY

# 3. Start with Docker Compose
cd docker && docker-compose up -d

# 4. Run migrations
docker exec apex_backend alembic upgrade head

# 5. Seed exercise database
docker exec apex_backend python -m scripts.seed_exercises

# 6. API is live at http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

## Local Development (without Docker)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
alembic upgrade head
python -m scripts.seed_exercises
uvicorn app.main:app --reload --port 8000
```

## Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | — | Register new user |
| POST | /api/auth/login | — | Login |
| POST | /api/auth/refresh | — | Refresh access token |
| POST | /api/auth/logout | — | Revoke refresh token |
| GET | /api/users/me | ✓ | Get current user |
| PUT | /api/users/me | ✓ | Update profile |
| POST | /api/metrics | ✓ | Log measurements |
| GET | /api/metrics | ✓ | Get measurements history |
| GET | /api/metrics/latest | ✓ | Get latest snapshot |
| GET | /api/metrics/{id} | ✓ | Get by ID |
| PUT | /api/metrics/{id} | ✓ | Update |
| DELETE | /api/metrics/{id} | ✓ | Delete |
| GET | /api/exercises | ✓ | List exercises (filterable) |
| GET | /api/exercises/{id} | ✓ | Get exercise |
| POST | /api/exercises | ✓ Admin | Create exercise |
| PUT | /api/exercises/{id} | ✓ Admin | Update exercise |
| DELETE | /api/exercises/{id} | ✓ Admin | Soft-delete exercise |
| GET | /api/training | ✓ | List training plans |
| GET | /api/training/{id} | ✓ | Get plan with exercises |
| POST | /api/training | ✓ | Create custom plan |
| POST | /api/training/generate | ✓ | Generate from template |
| PUT | /api/training/{id} | ✓ | Update plan |
| DELETE | /api/training/{id} | ✓ | Delete plan |
| GET | /api/health | — | Health check |

## ML Integration (Future)

The `app/ml/` directory is structured for future ML integration:

```
app/ml/
├── prediction/
│   └── physique_predictor.py  # Abstract interface — implement here
├── models/                     # Saved model weights (.pkl, .pt, etc.)
├── training/                   # Training scripts
└── datasets/                   # Dataset management
```

When adding ML, implement `BasePhysiquePredictor` in
`app/ml/prediction/physique_predictor.py` and inject it into
`TrainingService.generate_from_template()`.
