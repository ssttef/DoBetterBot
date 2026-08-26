from datetime import datetime, timezone
from sqlalchemy import BigInteger, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """The foundational class for all database models."""
    pass

class User(Base):
    __tablename__ = "users"

    # Discord IDs are massive numbers, so we use BigInteger, not regular Integer
    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_timezone: Mapped[str] = mapped_column(String, default="UTC")
    freezes_available: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    #"One user can have many habits."
    habits: Mapped[list["Habit"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # These relationships link the tables together in Python memory
    user: Mapped["User"] = relationship(back_populates="habits")
    logs: Mapped[list["HabitLog"]] = relationship(back_populates="habit", cascade="all, delete-orphan")

class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Link back to the habit
    habit: Mapped["Habit"] = relationship(back_populates="logs")
class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"))
    achievement_name: Mapped[str] = mapped_column(String, nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="achievements")