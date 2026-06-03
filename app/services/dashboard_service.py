from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.repositories.training_repository import TrainingPlanRepository
from app.repositories.focus_area_repository import FocusAreaRepository
from app.repositories.event_repository import EventRepository
from app.schemas.dashboard import DashboardSummary, EventCountdown
from app.schemas.training import TrainingPlanSummary


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.training_repo = TrainingPlanRepository(session)
        self.focus_repo = FocusAreaRepository(session)
        self.event_repo = EventRepository(session)

    async def get_summary(self, user_id: int) -> DashboardSummary:
        user = await self.user_repo.get_by_id_with_profile(user_id)
        goal = user.profile.fitness_goal if user and user.profile else None

        focus_items = await self.focus_repo.get_by_user(user_id)
        focus_area_names = [f.focus_area for f in focus_items]

        upcoming = await self.event_repo.get_next_upcoming(user_id)
        event_countdown: EventCountdown | None = None
        if upcoming:
            now = datetime.now(timezone.utc)
            target = upcoming.event_date if upcoming.event_date.tzinfo else \
                upcoming.event_date.replace(tzinfo=timezone.utc)
            days_remaining = max(0, (target - now).days)
            event_countdown = EventCountdown(
                id=upcoming.id,
                event_name=upcoming.event_name,
                event_type=upcoming.event_type,
                event_date=upcoming.event_date,
                days_remaining=days_remaining,
            )

        active_plan = await self.training_repo.get_active_by_user(user_id)
        plan_summary = (
            TrainingPlanSummary.model_validate(active_plan) if active_plan else None
        )

        return DashboardSummary(
            goal=goal,
            focus_areas=focus_area_names,
            event=event_countdown,
            current_training_plan=plan_summary,
        )
