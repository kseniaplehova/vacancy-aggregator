from .base import Source
from .belmeta import Belmeta
from .devby import DevBy
from .myjob import MyJob
from .rabota_by import RabotaBy

#: все подключённые источники; новый источник добавляется одной строкой
ALL_SOURCES: list[type[Source]] = [RabotaBy, DevBy, Belmeta, MyJob]

__all__ = ["ALL_SOURCES", "Source", "Belmeta", "DevBy", "MyJob", "RabotaBy"]
