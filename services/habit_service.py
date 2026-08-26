from datetime import datetime
from zoneinfo import ZoneInfo
from database.models import HabitLog
from sqlalchemy import select, func
from database.connection import SessionLocal
from database.models import User, Habit

async def create_new_habit(discord_id: int, habit_name: str) -> tuple[bool, str]:
    """
    Creates a habit. Returns (Success Boolean, Message String).
    """
    async with SessionLocal() as session:
        # 1. Check if the user exists in our database. If not, create them.
        user = await session.get(User, discord_id)
        if not user:
            user = User(discord_id=discord_id)
            session.add(user)
            await session.commit()

        # 2. DUPLICATE CHECK: Case-insensitive search
        duplicate_check = await session.execute(
            select(Habit).where(
                Habit.user_id == discord_id,
                func.lower(Habit.name) == habit_name.lower()
            )
        )
        if duplicate_check.scalar():
            return False, f"You already have a habit resembling '{habit_name}'. Don't play games with me."

        # 3. Check how many habits they currently have
        result = await session.execute(
            select(func.count(Habit.id)).where(Habit.user_id == discord_id)
        )
        habit_count = result.scalar()

        # 4. Enforce the limit
        if habit_count >= 10:
            return False, "You already have 10 habits. Focus on what you have before adding more."

        # 5. Create the habit
        new_habit = Habit(user_id=discord_id, name=habit_name)
        session.add(new_habit)
        await session.commit()

        return True, habit_name
async def get_user_habits(discord_id: int):
    """
    Fetches all habits for a specific user, sorted by highest streak first.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Habit)
            .where(Habit.user_id == discord_id)
            .order_by(Habit.current_streak.desc())
        )
        return result.scalars().all()


async def log_habit(discord_id: int, habit_id: int) -> tuple[bool, str, dict]:
    """
    Logs a habit and returns (Success, Message, EventData).
    """
    tz = ZoneInfo("Europe/Bucharest")
    today = datetime.now(tz).date()
    event_data = {"freeze_used": False, "lost_streak": 0}

    async with SessionLocal() as session:
        habit = await session.get(Habit, habit_id)
        user = await session.get(User, discord_id)

        if not habit or habit.user_id != discord_id:
            return False, "This habit does not belong to you.", event_data

        last_log_query = await session.execute(
            select(HabitLog).where(HabitLog.habit_id == habit_id).order_by(HabitLog.completed_at.desc()).limit(1)
        )
        last_log = last_log_query.scalar_one_or_none()

        status_message = ""

        if not last_log:
            habit.current_streak = 1
            status_message = f"Day 1 for '{habit.name}'. Don't quit tomorrow."
        else:
            last_date = last_log.completed_at.astimezone(tz).date()
            days_passed = (today - last_date).days

            if days_passed == 0:
                return False, f"You already logged '{habit.name}' today. Stop trying to cheat the grind.", event_data

            elif days_passed == 1:
                habit.current_streak += 1
                status_message = f"'{habit.name}' logged. Streak is now {habit.current_streak}. Keep moving forward."

            elif days_passed == 2 and user.freezes_available > 0:
                user.freezes_available -= 1
                habit.current_streak += 1
                event_data["freeze_used"] = True
                status_message = f"You missed yesterday. A Freeze was consumed ({user.freezes_available} left). Streak saved and increased to {habit.current_streak}."

            else:
                old_streak = habit.current_streak
                if old_streak > 0:
                    event_data["lost_streak"] = old_streak

                habit.current_streak = 1
                status_message = f"You let your {old_streak}-day streak die because of excuses. Back to day 1 for '{habit.name}'. Do better."

        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak

        new_log = HabitLog(habit_id=habit.id)
        session.add(new_log)
        await session.commit()

        return True, status_message, event_data


async def delete_habit(discord_id: int, habit_id: int) -> tuple[bool, str]:
    """
    Permanently deletes a habit and all its history from the database.
    """
    async with SessionLocal() as session:
        # 1. Fetch the habit
        habit = await session.get(Habit, habit_id)

        # 2. Security check: Make sure it exists and belongs to the user
        if not habit or habit.user_id != discord_id:
            return False, "You can't delete a habit that doesn't belong to you."

        habit_name = habit.name  # Save the name before we destroy it

        # 3. Destroy it (Cascades will automatically delete the logs)
        await session.delete(habit)
        await session.commit()

        return True, f"Habit '{habit_name}' and all its history have been permanently erased. Weak."