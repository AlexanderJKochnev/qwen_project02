# app.support.migration.schemas

from app.core.schemas.base import CreateSchema, ReadSchema, UpdateSchema, CreateResponse, DetailView


class CustomReadSchema:
    pass


class CustomCreateSchema:
    pass


class CustomCreateRelation:
    pass


class CustomUpdSchema:
    pass


class MigrationRead(ReadSchema, CustomReadSchema):
    pass


class MigrationReadRelation(ReadSchema, CustomReadSchema):
    pass


class MigrationCreateRelation(CreateSchema, CustomCreateRelation):
    pass


class MigrationCreate(CreateSchema, CustomCreateSchema):
    pass


class MigrationUpdate(UpdateSchema, CustomUpdSchema):
    pass


class MigrationCreateResponseSchema(MigrationCreate, CreateResponse):
    pass


class MigrationDetailView(DetailView):
    pass
