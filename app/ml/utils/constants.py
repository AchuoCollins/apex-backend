"""
app/ml/utils/constants.py

Sports science aesthetic ratio targets and configuration constants.
Based on classical physique research (Steve Reeves, Golden Ratio studies)
and modern hypertrophy literature.
"""

# ── Aesthetic Ratio Targets ───────────────────────────────────────────────────

GOLDEN_RATIO = 1.618

RATIO_TARGETS = {
    "shoulder_to_waist": 1.618,   # Golden ratio — most important aesthetic proportion
    "chest_to_waist":    1.40,    # Full chest relative to waist
    "hip_to_waist":      1.25,    # Classic X-frame taper
    "thigh_to_waist":    0.75,    # Lower body proportion
    "calf_to_thigh":     0.60,    # Lower leg symmetry
    "arm_to_neck":       1.00,    # Upper arm ≈ neck circumference
    "forearm_to_arm":    0.80,    # Forearm development
}

# Tolerance bands — within this % of target = "optimal"
OPTIMAL_BAND_PCT   = 5.0   # ±5% of target = optimal
DEVELOPING_LOW_PCT = 85.0  # 85–95% of target = developing
LAGGING_THRESHOLD  = 85.0  # < 85% of target = lagging

# ── Score Weights ─────────────────────────────────────────────────────────────
# Relative importance of each ratio in the overall physique score

RATIO_WEIGHTS = {
    "shoulder_to_waist": 0.30,   # Most visually impactful
    "chest_to_waist":    0.15,
    "hip_to_waist":      0.10,
    "thigh_to_waist":    0.15,
    "calf_to_thigh":     0.10,
    "arm_to_neck":       0.12,
    "forearm_to_arm":    0.08,
}

# ── Muscle Group → Ratio Mapping ─────────────────────────────────────────────

MUSCLE_TO_RATIO = {
    "shoulders": "shoulder_to_waist",
    "chest":     "chest_to_waist",
    "glutes":    "hip_to_waist",
    "quads":     "thigh_to_waist",
    "calves":    "calf_to_thigh",
    "biceps":    "arm_to_neck",
    "triceps":   "arm_to_neck",
    "forearms":  "forearm_to_arm",
}

RATIO_TO_PRIMARY_MUSCLE = {
    "shoulder_to_waist": "Shoulders",
    "chest_to_waist":    "Chest",
    "hip_to_waist":      "Glutes",
    "thigh_to_waist":    "Quads",
    "calf_to_thigh":     "Calves",
    "arm_to_neck":       "Arms",
    "forearm_to_arm":    "Forearms",
}

# ── Volume Targets (sets/week) by Experience ──────────────────────────────────

VOLUME_TARGETS = {
    "beginner": {
        "maintenance": 10,
        "hypertrophy": 15,
        "specialisation": 20,
    },
    "intermediate": {
        "maintenance": 12,
        "hypertrophy": 18,
        "specialisation": 25,
    },
    "advanced": {
        "maintenance": 16,
        "hypertrophy": 22,
        "specialisation": 32,
    },
}

# ── Status Labels ─────────────────────────────────────────────────────────────

STATUS_OPTIMAL      = "optimal"
STATUS_DEVELOPING   = "developing"
STATUS_LAGGING      = "lagging"
STATUS_OVERDEVELOPED = "overdeveloped"

PRIORITY_HIGH   = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW    = "low"
