from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class RawVacancy:
    source: str
    source_id: str
    url: str
    title: str
    company: str | None = None
    city: str | None = None
    salary: str | None = None
    description: str | None = None
    published: str | None = None
    origin: str | None = None
    origin_url: str | None = None
    detailed: bool = False
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["collected_at"] = self.collected_at.isoformat()
        return data
