# app/support/__init__.py
"""
    порядок импорта определяет порядок загрузки
    модели с ForeignKey должны должны быть выше моделей на которые они ссылаются
"""
# flake8: noqa: F401
from app.support.varietal.model import Varietal
from app.support.item.model import Item
from app.support.drink.model import Drink
from app.support.category.model import Category
from app.support.subcategory.model import Subcategory
from app.support.food.model import Food
from app.support.superfood.model import Superfood
from app.support.subregion.model import Subregion
from app.support.region.model import Region
from app.support.country.model import Country
from app.support.sweetness.model import Sweetness
from app.support.warehouse.model import Warehouse
from app.support.customer.model import Customer
from app.support.parser.model import Name, Code, Rawdata, Image, Status

from app.support.varietal.schemas import VarietalRead
from app.support.item.schemas import (ItemRead, ItemCreate, ItemUpdate,
                                      ItemCreateRelation, ItemReadRelation)
from app.support.drink.schemas import DrinkRead
from app.support.category.schemas import (CategoryRead, CategoryReadRelation,
                                          CategoryCreate, CategoryUpdate, CategoryCreateResponseSchema)
from app.support.subcategory.schemas import SubcategoryRead
from app.support.food.schemas import FoodRead
from app.support.superfood.schemas import SuperfoodRead
from app.support.region.schemas import RegionRead
from app.support.subregion.schemas import SubregionRead
from app.support.country.schemas import CountryRead
from app.support.sweetness.schemas import SweetnessRead
from app.support.warehouse.schemas import WarehouseRead
from app.support.customer.schemas import CustomerRead
from app.support.parser.schemas import (StatusCreate, StatusCreateResponseSchema, StatusRead, StatusUpdate,
                                        CodeCreate, CodeCreateResponseSchema, CodeRead, CodeUpdate,
                                        NameCreate, NameCreateResponseSchema, NameRead, NameUpdate,
                                        ImageCreate, ImageCreateResponseSchema, ImageRead, ImageUpdate,
                                        RawdataCreate, RawdataCreateResponseSchema,RawdataRead, RawdataUpdate)


from app.support.category.service import CategoryService
from app.support.country.service import CountryService
from app.support.item.service import ItemService
from app.support.customer.service import CustomerService
from app.support.drink.service import DrinkService
from app.support.food.service import FoodService
from app.support.region.service import RegionService
from app.support.subcategory.service import SubcategoryService
from app.support.subregion.service import SubregionService
from app.support.superfood.service import SuperfoodService
from app.support.sweetness.service import SweetnessService
from app.support.varietal.service import VarietalService
from app.support.parser.service import StatusService, CodeService,  NameService, ImageService, RawdataService

# from app.support.warehouse.service import WarehouseService
from app.support.warehouse.repository import WarehouseRepository
from app.support.parser.repository import (StatusRepository, CodeRepository, NameRepository, ImageRepository,
                                           RawdataRepository)

__all__ = [CategoryRead, CategoryReadRelation, CategoryCreate, CategoryUpdate, CategoryCreateResponseSchema,
           ItemRead, ItemCreate, ItemUpdate, ItemCreateRelation, ItemReadRelation, WarehouseRepository
           ]
