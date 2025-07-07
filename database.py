from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import ssl
ssl_context = ssl.create_default_context()

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_MgdZBRh8D3oU@ep-plain-band-a1ny55ux-pooler.ap-southeast-1.aws.neon.tech/neondb"

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"ssl": ssl_context})
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
