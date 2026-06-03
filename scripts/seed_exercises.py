"""
scripts/seed_exercises.py
Run: python -m scripts.seed_exercises
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.exercise import Exercise, MuscleGroup, Difficulty, Equipment, ExerciseType

EXERCISES = [
    # ── Chest ────────────────────────────────────────────────────────────────
    ("Flat Barbell Bench Press",    MuscleGroup.CHEST,     Difficulty.BEGINNER,     Equipment.BARBELL,    ExerciseType.COMPOUND,  "Classic horizontal press targeting the pectorals."),
    ("Incline Barbell Press",       MuscleGroup.CHEST,     Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "Emphasises upper chest with a 30-45 degree incline."),
    ("Flat Dumbbell Press",         MuscleGroup.CHEST,     Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.COMPOUND,  "Greater range of motion than barbell press."),
    ("Incline Dumbbell Press",      MuscleGroup.CHEST,     Difficulty.INTERMEDIATE, Equipment.DUMBBELL,   ExerciseType.COMPOUND,  "Upper chest emphasis with independent arm movement."),
    ("Flat Dumbbell Flye",          MuscleGroup.CHEST,     Difficulty.INTERMEDIATE, Equipment.DUMBBELL,   ExerciseType.ISOLATION, "Chest isolation through horizontal adduction."),
    ("Cable Crossover",             MuscleGroup.CHEST,     Difficulty.INTERMEDIATE, Equipment.CABLE,      ExerciseType.ISOLATION, "Constant tension chest isolation."),
    ("Push-Up",                     MuscleGroup.CHEST,     Difficulty.BEGINNER,     Equipment.BODYWEIGHT, ExerciseType.COMPOUND,  "Foundational pressing movement."),
    # ── Back ─────────────────────────────────────────────────────────────────
    ("Barbell Row",                 MuscleGroup.BACK,      Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "Primary horizontal pulling movement."),
    ("Weighted Pull-Up",            MuscleGroup.BACK,      Difficulty.ADVANCED,     Equipment.BODYWEIGHT, ExerciseType.COMPOUND,  "Best lat width builder — add weight when bodyweight is easy."),
    ("Lat Pulldown",                MuscleGroup.BACK,      Difficulty.BEGINNER,     Equipment.CABLE,      ExerciseType.COMPOUND,  "Vertical pull targeting the latissimus dorsi."),
    ("Seated Cable Row",            MuscleGroup.BACK,      Difficulty.BEGINNER,     Equipment.CABLE,      ExerciseType.COMPOUND,  "Horizontal pull with constant cable tension."),
    ("Straight-Arm Pulldown",       MuscleGroup.BACK,      Difficulty.INTERMEDIATE, Equipment.CABLE,      ExerciseType.ISOLATION, "Isolates lats through shoulder extension."),
    ("Dumbbell Row",                MuscleGroup.BACK,      Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.COMPOUND,  "Unilateral horizontal pull."),
    ("Deadlift",                    MuscleGroup.BACK,      Difficulty.ADVANCED,     Equipment.BARBELL,    ExerciseType.COMPOUND,  "King of all posterior chain movements."),
    # ── Shoulders ────────────────────────────────────────────────────────────
    ("Overhead Press",              MuscleGroup.SHOULDERS, Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "Primary vertical pressing movement for shoulder mass."),
    ("Dumbbell Shoulder Press",     MuscleGroup.SHOULDERS, Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.COMPOUND,  "Seated or standing overhead press with dumbbells."),
    ("Lateral Raise",               MuscleGroup.SHOULDERS, Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.ISOLATION, "Side deltoid isolation for shoulder width."),
    ("Face Pull",                   MuscleGroup.SHOULDERS, Difficulty.BEGINNER,     Equipment.CABLE,      ExerciseType.ISOLATION, "Rear delt and rotator cuff health exercise."),
    # ── Biceps ───────────────────────────────────────────────────────────────
    ("Barbell Curl",                MuscleGroup.BICEPS,    Difficulty.BEGINNER,     Equipment.BARBELL,    ExerciseType.ISOLATION, "Standard bilateral bicep curl."),
    ("Incline Dumbbell Curl",       MuscleGroup.BICEPS,    Difficulty.INTERMEDIATE, Equipment.DUMBBELL,   ExerciseType.ISOLATION, "Long head stretch position for peak development."),
    ("Hammer Curl",                 MuscleGroup.BICEPS,    Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.ISOLATION, "Neutral grip targets brachialis and brachioradialis."),
    # ── Triceps ──────────────────────────────────────────────────────────────
    ("Close-Grip Bench Press",      MuscleGroup.TRICEPS,   Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "Best compound tricep mass builder."),
    ("Cable Tricep Pushdown",       MuscleGroup.TRICEPS,   Difficulty.BEGINNER,     Equipment.CABLE,      ExerciseType.ISOLATION, "Standard tricep isolation with cable."),
    ("Overhead Tricep Extension",   MuscleGroup.TRICEPS,   Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.ISOLATION, "Long head emphasis in stretched position."),
    # ── Legs ─────────────────────────────────────────────────────────────────
    ("Barbell Back Squat",          MuscleGroup.LEGS,      Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "King of leg exercises — primary quad and glute builder."),
    ("Romanian Deadlift",           MuscleGroup.LEGS,      Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "Primary hamstring and glute hinge movement."),
    ("Leg Press",                   MuscleGroup.LEGS,      Difficulty.BEGINNER,     Equipment.MACHINE,    ExerciseType.COMPOUND,  "Machine squat variation for quad and glute hypertrophy."),
    ("Leg Curl",                    MuscleGroup.LEGS,      Difficulty.BEGINNER,     Equipment.MACHINE,    ExerciseType.ISOLATION, "Hamstring isolation."),
    ("Leg Extension",               MuscleGroup.LEGS,      Difficulty.BEGINNER,     Equipment.MACHINE,    ExerciseType.ISOLATION, "Quad isolation."),
    ("Bulgarian Split Squat",       MuscleGroup.LEGS,      Difficulty.ADVANCED,     Equipment.DUMBBELL,   ExerciseType.COMPOUND,  "Unilateral leg exercise for quad and glute development."),
    ("Goblet Squat",                MuscleGroup.LEGS,      Difficulty.BEGINNER,     Equipment.DUMBBELL,   ExerciseType.COMPOUND,  "Beginner-friendly squat variation."),
    ("Hip Thrust",                  MuscleGroup.LEGS,      Difficulty.INTERMEDIATE, Equipment.BARBELL,    ExerciseType.COMPOUND,  "Primary glute builder."),
    # ── Calves ───────────────────────────────────────────────────────────────
    ("Standing Calf Raise",         MuscleGroup.CALVES,    Difficulty.BEGINNER,     Equipment.MACHINE,    ExerciseType.ISOLATION, "Primary gastrocnemius builder."),
    ("Seated Calf Raise",           MuscleGroup.CALVES,    Difficulty.BEGINNER,     Equipment.MACHINE,    ExerciseType.ISOLATION, "Targets the soleus with bent-knee position."),
    # ── Core ─────────────────────────────────────────────────────────────────
    ("Ab Wheel Rollout",            MuscleGroup.CORE,      Difficulty.INTERMEDIATE, Equipment.OTHER,      ExerciseType.COMPOUND,  "Full core tension through anti-extension."),
    ("Cable Crunch",                MuscleGroup.CORE,      Difficulty.BEGINNER,     Equipment.CABLE,      ExerciseType.ISOLATION, "Weighted crunch with constant cable tension."),
    ("Plank",                       MuscleGroup.CORE,      Difficulty.BEGINNER,     Equipment.BODYWEIGHT, ExerciseType.ISOLATION, "Isometric core stability hold."),
]


async def seed():
    async with AsyncSessionLocal() as session:
        for name, muscle, diff, equip, ex_type, desc in EXERCISES:
            existing = await session.execute(
                __import__('sqlalchemy', fromlist=['select']).select(Exercise).where(Exercise.name == name)
            )
            if existing.scalar_one_or_none():
                print(f"  skip (exists): {name}")
                continue

            exercise = Exercise(
                name=name,
                muscle_group=muscle,
                difficulty=diff,
                equipment=equip,
                exercise_type=ex_type,
                description=desc,
            )
            session.add(exercise)
            print(f"  added: {name}")

        await session.commit()
        print(f"\nDone — {len(EXERCISES)} exercises processed.")


if __name__ == "__main__":
    asyncio.run(seed())
