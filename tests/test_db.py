import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from vacancy_aggregator.db import VacancyRow, create_engine, init_db, save_vacancies
from vacancy_aggregator.models import Vacancy


def vacancy(source_id="1", source="rabota.by", **fields):
    return Vacancy(source=source, source_id=source_id, url="https://example.org/1", title="Python Developer", **fields)


def test_save_adds_then_updates(tmp_path):
    async def scenario():
        engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
        await init_db(engine)

        first = await save_vacancies(engine, [vacancy("1", description="полный текст"), vacancy("2")])
        # повторный сбор: та же вакансия без описания, одна новая и вакансия с тем же номером из другого источника
        second = await save_vacancies(
            engine, [vacancy("1", salary="от 4 000 BYN"), vacancy("3"), vacancy("1", source="belmeta.com")]
        )

        async with async_sessionmaker(engine)() as session:
            total = await session.scalar(select(func.count()).select_from(VacancyRow))
            row = await session.scalar(
                select(VacancyRow).where(VacancyRow.source == "rabota.by", VacancyRow.source_id == "1")
            )
        await engine.dispose()
        return first, second, total, row

    first, second, total, row = asyncio.run(scenario())
    assert first == (2, 0)
    assert second == (2, 1)
    assert total == 4
    assert row.salary == "от 4 000 BYN"
    assert row.description == "полный текст"  # не затёрлось пустым значением
    assert row.last_seen > row.first_seen
