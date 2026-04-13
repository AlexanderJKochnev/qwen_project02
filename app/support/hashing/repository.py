# app/support/hashing/repository.py
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.hashing.model import WordHash


class WordHashRepository(Repository):
    model = WordHash
