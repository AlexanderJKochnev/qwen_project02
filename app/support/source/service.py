# app.support.source.servic.py

from app.core.services.service import Service
from app.support.source.repository import SourceRepository  # NOQA: F401


class SourceService(Service):
    default: list = ['name']
