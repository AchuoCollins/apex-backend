from io import BytesIO
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

from app.core.exceptions import NotFoundException
from app.models.training_plan import TrainingPlan
from app.repositories.training_repository import TrainingPlanRepository
from app.repositories.user_repository import UserRepository
from app.repositories.focus_area_repository import FocusAreaRepository
from app.repositories.event_repository import EventRepository

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class TrainingPlanPDFService:
    """Generates a downloadable PDF for a training plan."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.training_repo = TrainingPlanRepository(session)
        self.user_repo = UserRepository(session)
        self.focus_repo = FocusAreaRepository(session)
        self.event_repo = EventRepository(session)

    async def generate(self, plan_id: int, user_id: int) -> tuple[BytesIO, str]:
        plan = await self.training_repo.get_by_id_with_exercises(plan_id, user_id)
        if not plan:
            raise NotFoundException("Training plan", plan_id)

        user = await self.user_repo.get_by_id_with_profile(user_id)
        focus_areas = await self.focus_repo.get_by_user(user_id)
        next_event = await self.event_repo.get_next_upcoming(user_id)

        buffer = BytesIO()
        self._render(buffer, plan, user, focus_areas, next_event)
        buffer.seek(0)

        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in plan.name)
        filename = f"training_plan_{plan.id}_{safe_name[:40]}.pdf"
        return buffer, filename

    def _render(self, buffer: BytesIO, plan: TrainingPlan, user, focus_areas, next_event) -> None:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=1.8 * cm, bottomMargin=1.8 * cm,
            title=plan.name,
        )

        styles = getSampleStyleSheet()
        h_style = ParagraphStyle("APEXHeading", parent=styles["Heading1"], textColor=colors.HexColor("#1f2933"))
        h2_style = ParagraphStyle("APEXSub", parent=styles["Heading2"], textColor=colors.HexColor("#3a4750"))
        body = styles["BodyText"]

        story = []
        story.append(Paragraph(f"APEX Training Plan", h_style))
        story.append(Paragraph(plan.name, h2_style))
        story.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            body,
        ))
        story.append(Spacer(1, 0.4 * cm))

        # ── User Information ─────────────────────────────────────────────────
        story.append(Paragraph("User Information", h2_style))
        profile = getattr(user, "profile", None)
        user_rows = [
            ["Name", f"{user.first_name} {user.last_name}"],
            ["Email", user.email],
        ]
        if profile is not None:
            if profile.gender is not None:
                user_rows.append(["Gender", profile.gender.value])
            if profile.age is not None:
                user_rows.append(["Age", str(profile.age)])
            if profile.height_cm is not None:
                user_rows.append(["Height", f"{profile.height_cm:.1f} cm"])
            if profile.weight_kg is not None:
                user_rows.append(["Weight", f"{profile.weight_kg:.1f} kg"])
            if profile.experience_level is not None:
                user_rows.append(["Experience", profile.experience_level.value.title()])
            if profile.training_reason is not None:
                user_rows.append(["Training Reason", profile.training_reason.value.replace("_", " ").title()])
        story.append(self._kv_table(user_rows))
        story.append(Spacer(1, 0.4 * cm))

        # ── Goal ─────────────────────────────────────────────────────────────
        story.append(Paragraph("Goal", h2_style))
        story.append(Paragraph(plan.goal.value.replace("_", " ").title(), body))
        story.append(Spacer(1, 0.3 * cm))

        # ── Focus Areas ──────────────────────────────────────────────────────
        story.append(Paragraph("Focus Areas", h2_style))
        if focus_areas:
            story.append(Paragraph(", ".join(f.focus_area for f in focus_areas), body))
        else:
            story.append(Paragraph("—", body))
        story.append(Spacer(1, 0.3 * cm))

        # ── Event Information ────────────────────────────────────────────────
        story.append(Paragraph("Event Information", h2_style))
        if next_event:
            event_rows = [
                ["Event", next_event.event_name],
                ["Type", next_event.event_type.value.replace("_", " ").title()],
                ["Date", next_event.event_date.strftime("%Y-%m-%d")],
            ]
            now = datetime.now(timezone.utc)
            target = next_event.event_date if next_event.event_date.tzinfo else \
                next_event.event_date.replace(tzinfo=timezone.utc)
            days_left = max(0, (target - now).days)
            event_rows.append(["Countdown", f"{days_left} days"])
            story.append(self._kv_table(event_rows))
        else:
            story.append(Paragraph("No upcoming event.", body))
        story.append(Spacer(1, 0.5 * cm))

        # ── Weekly Split ─────────────────────────────────────────────────────
        story.append(Paragraph("Weekly Split", h2_style))
        story.append(Paragraph(
            f"{plan.workout_split.value.replace('_', ' ').title()} — "
            f"{plan.days_per_week} days/week — {plan.duration_weeks} weeks",
            body,
        ))
        story.append(Spacer(1, 0.3 * cm))

        # ── Exercises grouped by day ─────────────────────────────────────────
        exercises_by_day: dict[int, list] = {}
        for pe in plan.exercises:
            exercises_by_day.setdefault(pe.day_of_week, []).append(pe)

        if not exercises_by_day:
            story.append(Paragraph("No exercises configured.", body))
        else:
            for day in sorted(exercises_by_day.keys()):
                day_name = DAY_NAMES[day - 1] if 1 <= day <= 7 else f"Day {day}"
                story.append(Paragraph(f"Day {day} — {day_name}", h2_style))

                rows = [["#", "Exercise", "Muscle", "Sets", "Reps", "Rest"]]
                day_items = sorted(exercises_by_day[day], key=lambda x: x.order_in_session)
                for pe in day_items:
                    rows.append([
                        str(pe.order_in_session),
                        pe.exercise.name,
                        pe.exercise.muscle_group.value.title(),
                        str(pe.sets),
                        f"{pe.reps_min}-{pe.reps_max}",
                        f"{pe.rest_seconds}s",
                    ])
                table = Table(rows, hAlign="LEFT", colWidths=[1*cm, 6*cm, 3*cm, 1.5*cm, 2*cm, 1.5*cm])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2933")),
                    ("TEXTCOLOR",  (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0, 0), (-1, -1), 9),
                    ("GRID",       (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.4 * cm))

        doc.build(story)

    @staticmethod
    def _kv_table(rows: list[list[str]]) -> Table:
        table = Table(rows, hAlign="LEFT", colWidths=[4 * cm, 12 * cm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return table
