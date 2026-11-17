import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, String, Text, UniqueConstraint, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .models import Vacancy

#: адрес базы берётся из переменной окружения; по умолчанию — файл SQLite.
#: Для PostgreSQL достаточно задать postgresql+asyncpg://пользователь:пароль@хост/база
DEFAULT_URL = "sqlite+aiosqlite:///data/vacancies.db"

#: поля, которые при повторном сборе обновляются данными источника
UPDATED_FIELDS = ("url", "title", "company", "city", "salary", "description", "published", "origin")


class Base(DeclarativeBase):
    pass


class VacancyRow(Base):
    __tablename__ = "vacancies"
    # одна и та же вакансия источника хранится один раз
    __table_args__ = (UniqueConstraint("source", "source_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    salary: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    published: Mapped[str | None] = mapped_column(String(64))
    origin: Mapped[str | None] = mapped_column(String(128))
    #: когда вакансия впервые попала в базу и когда в последний раз встретилась в источнике
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_URL)


def create_engine(url: str | None = None) -> AsyncEngine:
    url = url or database_url()
    database = make_url(url).database
    if url.startswith("sqlite") and database and database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(url)


async def init_db(engine: AsyncEngine) -> None:
    """Создаёт таблицы, если их ещё нет."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def save_vacancies(engine: AsyncEngine, vacancies: list[Vacancy]) -> tuple[int, int]:
    """Записывает вакансии в базу; возвращает число новых и число обновлённых.

    Вакансия, которая уже есть в базе (тот же источник и идентификатор),
    не дублируется: у неё обновляются поля и отметка «последний раз видели».
    """
    added = updated = 0
    now = datetime.now(timezone.utc)
    by_source: dict[str, dict[str, Vacancy]] = {}
    for vacancy in vacancies:
        by_source.setdefault(vacancy.source, {})[vacancy.source_id] = vacancy

    async with async_sessionmaker(engine)() as session, session.begin():
        for source, items in by_source.items():
            query = select(VacancyRow).where(VacancyRow.source == source, VacancyRow.source_id.in_(items))
            existing = {row.source_id: row for row in await session.scalars(query)}
            for source_id, vacancy in items.items():
                row = existing.get(source_id)
                if row is None:
                    row = VacancyRow(source=source, source_id=source_id, first_seen=now)
                    session.add(row)
                    added += 1
                else:
                    updated += 1
                for name in UPDATED_FIELDS:
                    value = getattr(vacancy, name)
                    # короткая карточка из списка не должна затирать уже сохранённое описание
                    if value is not None or getattr(row, name, None) is None:
                        setattr(row, name, value)
                row.last_seen = now
    return added, updated
