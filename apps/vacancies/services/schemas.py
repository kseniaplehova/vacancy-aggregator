from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class RawVacancy:
    """Вакансия в том виде, в каком её отдал источник.

    Зарплата и дата хранятся строкой: источники записывают их по-разному
    («от 4 000 BYN», «$1500—4000», «Сегодня»), разбор — отдельный этап.
    """

    source: str
    source_id: str
    url: str
    title: str
    company: str | None = None
    city: str | None = None
    salary: str | None = None
    description: str | None = None
    published: str | None = None
    #: площадка-первоисточник, если источник сам агрегатор и называет её
    origin: str | None = None
    #: адрес этой же вакансии на площадке-первоисточнике
    origin_url: str | None = None
    #: True — страница вакансии загружена, описание полное
    detailed: bool = False
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["collected_at"] = self.collected_at.isoformat()
        return data
