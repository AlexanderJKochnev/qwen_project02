# app.core.schemas.unused.md

Unused Pydantic Models
From app/support/customer/schemas.py:

    CustomReadSchema
    CustomCreateSchema
    CustomUpdSchema
    CustomerCreateRelation

From app/support/drink/drink_food_schema.py:

### DrinkDetailResponse (defined twice but not referenced elsewhere)

From app/support/drink/drink_varietal_schema.py:

### DrinkDetailResponse (defined twice but not referenced elsewhere)

From app/support/drink/schemas.py:

    CustomReadSchema
    CustomCreateSchema
    CustomUpdSchema
    CustomReadRelation
    CustomReadFlatSchema
    CustomCreateRelation
    CustomCreateDrinkItem
    DrinkCreateItems
    DrinkReadApi

From app/support/field_keys/schemas.py:

    FieldKeyBase

From app/support/item/schemas.py:

    CustomReadFlatSchema
    CustomReadSchema
    CustomCreateSchema
    CustomUpdSchema
    CustomReadRelation
    CustomCreateRelation
    DirectUploadSchema
    FileUpload
    ItemReadRelation
    ItemReadPreact
    ItemCreatePreact
    ItemReadPreactForUpdate
    ItemUpdatePreact
    ItemCreateResponseSchema
    ItemCreateRelation
    DrinkPreactDetailView
    DrinkPreactListView
    DrinkPreactUpdate
    DrinkPreactCreate
    ItemListView
    ItemDetailNonLocalized
    ItemDetailForeignLocalized
    ItemDetailLocalized
    ItemDetailManyToManyLocalized
    ItemDetailView
    ItemDrinkPreactSchema
    ItemApiLang
    ItemApiRoot
    ItemApi

From app/support/parser/schemas.py:

    StatusCreateRelation
    StatusCreateResponseSchema
    StatusReadRelation
    RegistryCreateRelation
    RegistryCreateResponseSchema
    RegistryReadRelation
    CodeCreateRelation
    CodeCreateResponseSchema
    CodeReadRelation
    NameCreateRelation
    NameCreateResponseSchema
    NameReadRelation
    RawdataCreateRelation
    RawdataCreateResponseSchema
    RawdataReadRelation
    ImageCreateRelation
    ImageCreateResponseSchema
    ImageReadRelation

From app/core/schemas/api_mixin.py:

    No unused models (LangMixin is used by other schemas)

From app/core/schemas/dynamic_model.py:

    No specific models defined (contains utility function)

From app/core/schemas/image_mixin.py:

    No unused models (ImageUrlMixin and ImageUrlMixinPath are used by other schemas)

From app/core/schemas/search_model.py:

    No unused models (all models in this file appear to be used)