from .base import Source
from .belmeta import Belmeta
from .devby import DevBy
from .greenhouse import Greenhouse
from .lever import Lever
from .myjob import MyJob
from .rabota_by import RabotaBy


def default_sources() -> list[Source]:
    """Все подключённые источники; новый добавляется одной строкой."""
    return [
        RabotaBy(),
        DevBy(),
        Belmeta(),
        MyJob(),
        Greenhouse("issoft"),
        Greenhouse("coherentsolutions"),
        Greenhouse("tripledotstudios"),
        Lever("idt", company="IDT"),
        Lever("SatelliteInnovations", company="Satellite Innovations"),
    ]


__all__ = ["default_sources", "Source", "Belmeta", "DevBy", "Greenhouse", "Lever", "MyJob", "RabotaBy"]
