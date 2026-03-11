# app.support.vintage.service.py
# from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
# from app.support.vintage.repository import VintageConfigRepository, DesignationRepository, ClassificationRepository
# from app.support.vintage.model import VintageConfig, Designation, Classification
# from app.support.vintage.schemas import (VintageConfigRead, VintageConfigCreate, VintageConfigUpdate,
#                                          ClassificationRead, ClassificationCreate, ClassificationUpdate,
#                                          DesignationCreate, DesignationRead, DesignationUpdate)


class VintageConfigService(Service):
    default: list = ['name']


class ClassificationService(Service):
    default: list = ['name']


class DesignationService(Service):
    default: list = ['name']
