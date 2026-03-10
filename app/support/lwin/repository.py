# app.support.lwin.repositpry.py
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.lwin.model import Lwin


class LwinRepository(Repository):
    model = Lwin