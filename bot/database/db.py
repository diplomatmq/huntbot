import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import inspect, text, select
from bot.config import DATABASE_URL

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def _migrate_species_from_json():
    from bot.database.models import User, AnimalSpecies
    from bot.game_logic.animals import get_animal_location

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.species_migrated == False)
        )
        users = result.scalars().all()
        if not users:
            return
        migrated_count = 0
        for user in users:
            try:
                combined = {}
                if user.animals_killed_free:
                    for k, v in user.animals_killed_free.items():
                        combined[k] = combined.get(k, 0) + int(v or 0)
                if user.animals_killed_story:
                    for k, v in user.animals_killed_story.items():
                        combined[k] = combined.get(k, 0) + int(v or 0)

                inserted_any = False
                for animal_key, count in combined.items():
                    if not count or count <= 0:
                        continue
                    name = animal_key
                    location = get_animal_location(name) or "forest"
                    exist = await session.execute(
                        select(AnimalSpecies).where(
                            AnimalSpecies.user_id == user.id,
                            AnimalSpecies.animal_name == name,
                            AnimalSpecies.location == location,
                        )
                    )
                    sp = exist.scalar_one_or_none()
                    if sp:
                        if sp.total_killed < count:
                            sp.total_killed = count
                            inserted_any = True
                    else:
                        sp_new = AnimalSpecies(
                            user_id=user.id,
                            animal_name=name,
                            location=location,
                            total_killed=int(count),
                        )
                        session.add(sp_new)
                        inserted_any = True
                user.species_migrated = True
                await session.commit()
                migrated_count += 1
            except Exception:
                await session.rollback()
                continue
        if migrated_count:
            print(f"Species migrated for {migrated_count} users")


async def add_missing_columns():
    from bot.database.models import (
        User, Inventory, Weapon, Quest, UserQuest,
        Animal, Trophy, AuctionLot, StarsTransaction, AnimalSpecies
    )

    async with engine.connect() as conn:
        def do_inspect(sync_conn):
            inspector = inspect(sync_conn)
            for table_name, table in Base.metadata.tables.items():
                try:
                    existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
                except Exception:
                    continue

                for column in table.columns:
                    column_name = column.name
                    if column_name not in existing_columns:
                        column_type = str(column.type.compile(dialect=sync_conn.dialect))
                        nullable = "NULL" if column.nullable else "NOT NULL"
                        default = ""
                        if column.default is not None:
                            default = f" DEFAULT {column.default.arg}" if not column.default.is_callable else ""

                        alter_sql = text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type} {nullable}{default}')
                        sync_conn.execute(alter_sql)
                        sync_conn.commit()
                        print(f"Added missing column '{column_name}' to table '{table_name}'")

        await conn.run_sync(do_inspect)

    await _migrate_species_from_json()


async def init_db():
    from bot.database.models import (
        User, Inventory, Weapon, Quest, UserQuest,
        Animal, Trophy, AuctionLot, StarsTransaction, AnimalSpecies
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await add_missing_columns()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
