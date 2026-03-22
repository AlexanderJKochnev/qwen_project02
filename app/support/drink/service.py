# app.support.drink.service.py
from typing import Optional, Type

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.sqlalchemy_repository import Repository
from app.core.services.service import ModelType, Service
from app.core.utils.alchemy_utils import model_to_dict
from app.core.utils.common_utils import flatten_dict
from app.support.drink.drink_food_repo import DrinkFoodRepository
from app.support.drink.drink_varietal_repo import DrinkVarietalRepository
from app.support.drink.model import Drink
from app.support.drink.repository import DrinkRepository
from app.support.drink.schemas import (DrinkCreate, DrinkCreateRelation, DrinkRead, DrinkUpdate)
from app.support.food.repository import FoodRepository
from app.support.food.service import FoodService
from app.support.parcel.model import Parcel, Site
from app.support.parcel.repository import ParcelRepository, SiteRepository
from app.support.parcel.service import ParcelService, SiteService
from app.support.producer.model import Producer
from app.support.producer.repository import ProducerRepository
from app.support.producer.service import ProducerService
from app.support.source.model import Source
from app.support.source.repository import SourceRepository
from app.support.source.service import SourceService
from app.support.subcategory.model import Subcategory
from app.support.subcategory.repository import SubcategoryRepository
from app.support.subcategory.service import SubcategoryService
from app.support.sweetness.model import Sweetness
from app.support.sweetness.repository import SweetnessRepository
from app.support.sweetness.service import SweetnessService
from app.support.varietal.model import Varietal
from app.support.varietal.repository import VarietalRepository
from app.support.varietal.service import VarietalService
from app.support.vintage.model import Classification, Designation, VintageConfig
from app.support.vintage.repository import ClassificationRepository, DesignationRepository, VintageConfigRepository
from app.support.vintage.service import ClassificationService, DesignationService, VintageConfigService


# from app.support.subregion.repository import SubregionRepository
# from app.support.subregion.service import SubregionService


class DrinkService(Service):
    """ переписываем методы для обрабоки manytomany relationships """
    __abstract__ = False
    #  список уникальных полей по которым определется существует запись или нет для update_or_create
    default = ['title', 'subtitle']

    @classmethod
    async def get_dict_by_id(cls, id: int, repository: Type[Repository],
                             model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        result = await super().get_by_id(id, repository, model, session)
        # return result

        try:
            subresult = model_to_dict(result)
            flatresult = flatten_dict(subresult, ['name', 'name_ru'])
            for key, val in subresult.items():
                pass
                # print(f'1.    {key}: {val}')
            for key, val in flatresult.items():
                pass
                # print(f'2.    {key}: {val}')
            return flatresult
        except Exception as e:
            print(f'drink.service..get_by_id error {e}')

    @classmethod
    async def create(cls, data: DrinkCreate, repository: Type[Repository],
                     model: Drink, session: AsyncSession, **kwargs) -> ModelType:
        """ create & return record """
        try:
            # remove unset and 'varietals', 'foods' items and back to pydantci schema
            data_dict: dict = data.model_dump(exclude={'varietals', 'food_associations'},
                                              exclude_unset=True)
            """
                "foods": [{"id": 5}, ...],
                "varietals": [{"varietal_id": 4,"percentage": null}, ...]
            """
            obj = DrinkCreate(**data_dict)
            drink_instance, created = await cls.get_or_create(obj, DrinkRepository, Drink, session)

            if not created:
                raise Exception(f"запись '{obj}' существует. Если необходимо обновить ее, "
                                f"воспользуйтесь формой 'Edit'")
            drink_id = drink_instance.id
            # добавляем drink_foods & drink_varietals
            if isinstance(data.food_associations, list):
                food_ids = [item.id for item in data.food_associations]
                await DrinkFoodRepository.set_drink_foods(drink_id, food_ids, session)
            if isinstance(data.varietals, list):
                # convert [{'id':4, 'percentage': null},...] -> {4: null, ...}
                varietal_percentage = {item.id: item.percentage for item in data.varietals}
                # add drink_id, varietal.ids to DrinkVarietal
                for key, val in varietal_percentage.items():
                    await DrinkVarietalRepository.add_varietal_to_drink(drink_id, key, val, session)
            await session.flush()
            await session.refresh(drink_instance)
            return drink_instance, created
        except Exception as e:
            raise Exception(f'drink_create_error: {e}')

    @classmethod
    async def patch(cls, id: int,
                    data: DrinkUpdate,
                    repository: Type[Repository],
                    model: ModelType, background_tasks: BackgroundTasks,
                    session: AsyncSession) -> dict:
        obj = await repository.get_by_id(id, model, session)
        if not obj:
            raise HTTPException(status_code=404, detail=f'drink.update запись c {id=} не найдена')
        data_dict = data.model_dump()
        varietals = data_dict.pop('varietals', None)
        foods = data_dict.pop('food_associations', None)

        # Filter out None values for required fields to prevent NOT NULL constraint violations
        # These fields are required in the database but optional in the schema
        filtered_data_dict = {}
        for key, value in data_dict.items():
            # Skip None values for required fields that have foreign key constraints
            if key in ['subcategory_id', 'subregion_id'] and value is None:
                continue
            filtered_data_dict[key] = value

        if varietals and isinstance(varietals, list):
            #  обновляем varietals
            #  заодно проверим правильность процентов (дополнить)
            varietal_dict = {var.get('id'): var.get('percentage', 0) for var in varietals}
            result = await DrinkVarietalRepository.set_drink_varietals_with_percentage(id, varietal_dict, session)
            if not result:
                raise HTTPException(status_code=500, detail=f'не удалось обновить varietals для drink {id=}')
        if foods and isinstance(foods, list):
            # [{'id': 91}, {'id': 114}]
            food_ids = [item.get('id') for item in foods]
            result = await DrinkFoodRepository.set_drink_foods(id, food_ids, session)
            if not result:
                raise HTTPException(status_code=500, detail=f'не удалось обновить foods для drink {id=}')
        result = await repository.patch(obj, filtered_data_dict, session)
        # await cls.run_backgound_task(id, background_tasks, True, repository, model, session)
        """ will be return:
            {"success": True, "data": obj}
            or
            {"success": False,
             "error_type": "unique_constraint_violation",
             "message": f"Нарушение уникальности: {original_error_str}",
             "field_info": field_info... !this field is Optional
             }
        """
        return result

    @classmethod
    async def create_relation(cls, data: DrinkCreateRelation,
                              repository: DrinkRepository, model: Drink,
                              session: AsyncSession, **kwargs) -> DrinkRead:
        source = {}
        source['site'] = (SiteRepository, Site, SiteService)
        source['subcategory'] = (SubcategoryRepository, Subcategory, SubcategoryService)
        source['sweetness'] = (SweetnessRepository, Sweetness, SweetnessService)
        source['source'] = (SourceRepository, Source, SourceService)
        source['producer'] = (ProducerRepository, Producer, ProducerService)
        source['vintageconfig'] = (VintageConfigRepository, VintageConfig, VintageConfigService)
        source['classification'] = (ClassificationRepository, Classification, ClassificationService)
        source['designation'] = (DesignationRepository, Designation, DesignationService)
        source['parcel'] = (ParcelRepository, Parcel, ParcelService)
        exclude_set = set(source.keys())
        data_dict: dict = data.model_dump(exclude=exclude_set, exclude_unset=True)
        for key, val in source.items():
            parent, parent_repo, parent_model, parent_service = val
            if parent_data := getattr(data, parent):
                result, _ = await parent_service.get_or_create(parent_data, parent_repo, parent_model, session)
                data_dict[f'{parent}_id'] = result.id
        drink_instance, _ = await cls.get_or_create(data_dict, repository, model, session)
        drink_id = drink_instance.id

        if isinstance(data.food_associations, list):
            food_ids = []
            # 1. get_or_create foods in Food
            for item in data.food_associations:
                result = await FoodService.create_relation(item, FoodRepository, FoodService, session)
                food_ids.append(result.id)
            # 2. set drink_food
            await DrinkFoodRepository.set_drink_foods(drink_id, food_ids, session)
        if isinstance(data.varietals, list):
            varietal_ids = []
            varietal_percentage = {}
            # 1. get_or_create varietals in Varietal
            # data.varietals is List[{varietal: VarietalCreateRelation
            #                         percentage: float}]
            for dvschema in data.varietals:
                item = dvschema.varietal
                percentage = dvschema.percentage
                result, _ = await VarietalService.get_or_create(item, VarietalRepository, Varietal, session)
                varietal_percentage[result.id] = percentage
                varietal_ids.append(result.id)
            # 2. set drink_varietal
            await DrinkVarietalRepository.set_drink_varietals(drink_id, varietal_ids, session)
            # 3. set up percentage
            for key, val in varietal_percentage.items():
                await DrinkVarietalRepository.update_percentage(drink_id, key, val, session)
        await session.flush()
        await session.refresh(drink_instance)
        return drink_instance
