from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from database.connection import SessionLocal
from database.models import UserAchievement, Habit, HabitLog



async def award_achievement_if_new(session, discord_id: int, achievement_name: str) -> bool:
    """
    Checks if the user has the achievement. If not, awards it and returns True.
    """
    query = await session.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == discord_id,
            UserAchievement.achievement_name == achievement_name
        )
    )
    exists = query.scalar_one_or_none()

    if not exists:
        new_achv = UserAchievement(user_id=discord_id, achievement_name=achievement_name)
        session.add(new_achv)
        return True
    return False
async def get_user_achievements(discord_id: int):
    """Fetches all unlocked achievements for a user."""
    async with SessionLocal() as session:
        query = await session.execute(
            select(UserAchievement).where(UserAchievement.user_id == discord_id)
        )
        return query.scalars().all()

async def check_specific_achievement(discord_id: int, name: str) -> bool:
    """Awards a specific achievement and returns True if newly unlocked."""
    async with SessionLocal() as session:
        if await award_achievement_if_new(session, discord_id, name):
            await session.commit()
            return True
        return False


async def check_log_achievements(discord_id: int, habit_id: int, event_data: dict) -> list[tuple[str, str]]:
    tz = ZoneInfo("Europe/Bucharest")
    now = datetime.now(tz)
    newly_unlocked = []

    async with SessionLocal() as session:
        habit = await session.get(Habit, habit_id)
        if not habit:
            return newly_unlocked

        # 1. The Procrastinator & Night Owl
        if now.hour == 23 and now.minute >= 50:
            if await award_achievement_if_new(session, discord_id, "The Procrastinator"):
                newly_unlocked.append(("The Procrastinator", "Cutting it close. Stop waiting until the last minute."))
        if 0 <= now.hour < 3:
            if await award_achievement_if_new(session, discord_id, "Night Owl"):
                newly_unlocked.append(("Night Owl", "While they sleep, you work."))

        # 2. Basic Streaks
        if habit.current_streak == 1:
            if await award_achievement_if_new(session, discord_id, "First Blood"):
                newly_unlocked.append(("First Blood", "Your first logged habit. Don't quit tomorrow."))
        if habit.current_streak == 7:
            if await award_achievement_if_new(session, discord_id, "The Foundation"):
                newly_unlocked.append(("The Foundation", "One week down. Don't ruin it now."))
        if habit.current_streak == 30:
            if await award_achievement_if_new(session, discord_id, "Iron Will"):
                newly_unlocked.append(("Iron Will", "A month of unbroken discipline."))
        if habit.current_streak == 100:
            if await award_achievement_if_new(session, discord_id, "The Machine"):
                newly_unlocked.append(("The Machine", "You are no longer relying on motivation."))

        # 3. Thin Ice (Freeze Used)
        if event_data.get("freeze_used"):
            if await award_achievement_if_new(session, discord_id, "Thin Ice"):
                newly_unlocked.append(("Thin Ice", "A freeze saved you. Do not let it happen again."))

        # 4. Back to Square One (Lost 10+ day streak)
        if event_data.get("lost_streak", 0) >= 10:
            if await award_achievement_if_new(session, discord_id, "Back to Square One"):
                newly_unlocked.append(("Back to Square One", "You let a 10+ day streak die. Weak."))

        # 5. Flawless Victory
        all_habits_query = await session.execute(select(Habit).where(Habit.user_id == discord_id))
        all_habits = all_habits_query.scalars().all()

        if len(all_habits) >= 3:
            flawless = True
            for h in all_habits:
                log_query = await session.execute(
                    select(HabitLog).where(HabitLog.habit_id == h.id).order_by(HabitLog.completed_at.desc()).limit(1)
                )
                last_log = log_query.scalar_one_or_none()
                if not last_log or last_log.completed_at.astimezone(tz).date() != now.date():
                    flawless = False
                    break

            if flawless:
                if await award_achievement_if_new(session, discord_id, "Flawless Victory"):
                    newly_unlocked.append(("Flawless Victory", "All active habits logged today. Perfect execution."))

        if newly_unlocked:
            await session.commit()

    return newly_unlocked