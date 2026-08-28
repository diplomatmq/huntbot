import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import inspect, text
from bot.config import DATABASE_URL

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def add_missing_columns():
    """Add missing columns to existing tables"""
    # Import models inside the function to avoid circular import
    from bot.database.models import (
        User, Inventory, Weapon, Quest, UserQuest,
        Animal, Trophy, AuctionLot, StarsTransaction
    )
    
    async with engine.connect() as conn:
        # Use a sync connection to run inspection
        def do_inspect(sync_conn):
            inspector = inspect(sync_conn)
            for table_name, table in Base.metadata.tables.items():
                # Get existing columns in the database
                try:
                    existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
                except Exception:
                    # Table doesn't exist yet, skip
                    continue
                
                # Check each column in the model
                for column in table.columns:
                    column_name = column.name
                    if column_name not in existing_columns:
                        # Generate ALTER TABLE statement
                        # Convert SQLAlchemy type to database type
                        column_type = str(column.type.compile(dialect=sync_conn.dialect))
                        nullable = "NULL" if column.nullable else "NOT NULL"
                        default = ""
                        if column.default is not None:
                            default = f" DEFAULT {column.default.arg}" if not column.default.is_callable else ""
                        
                        # SQLite doesn't support IF NOT EXISTS in ALTER TABLE, but we already checked column doesn't exist
                        alter_sql = text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type} {nullable}{default}')
                        sync_conn.execute(alter_sql)
                        sync_conn.commit()
                        print(f"Added missing column '{column_name}' to table '{table_name}'")
        
        await conn.run_sync(do_inspect)


async def init_db():
    # Import models first to register them with Base.metadata
    from bot.database.models import (
        User, Inventory, Weapon, Quest, UserQuest,
        Animal, Trophy, AuctionLot, StarsTransaction
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Add any missing columns
    await add_missing_columns()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
