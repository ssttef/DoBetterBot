import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base

# 1. Load the secrets from your .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from the .env file!")

# 2. The Engine: This is the actual vehicle that travels to PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=False)

# 3. The SessionMaker: This generates "workspaces" for our bot to query/save data
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 4. The initialization function to build our blueprint
async def init_db():
    """Creates all the tables in the database if they don't exist yet."""
    async with engine.begin() as conn:
        # This reads models.Base and tells PostgreSQL to build the tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully. No excuses. We are ready.")

# --- Temporary test block so you can run this file directly ---
if __name__ == "__main__":
    asyncio.run(init_db())