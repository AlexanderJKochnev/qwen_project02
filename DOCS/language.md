## Добавление языков;
0. .env
   1. LANGS=en,ru,fr,es,it,de,cn
1. app.core
   1. app.core.models
      1. app.core.models.base_model.py
         1. class BaseDescription: add/delete 
            #  description_xx
         2. class BaseLang(BaseDescription): add/delete 
            # name_xx
   2. app/core/schemas/base.py
      1. class DescriptionSchema(BaseModel): add/delete 
            # description_xx
      2. class NameSchema(BaseModel): 
            # add/delete name_xx
   3. app.support
      1. app/support/drink/model.py
         1. class Lang:
           # title_xx
           # subtitle_xx
           # description_xx
           # recommendation_xx
           # madeof_xx
           # description_xx[PyCharm CE.app](..%2F..%2F..%2F..%2F..%2F..%2FApplications%2FPyCharm%20CE.app)
      2. create_gin_index_sql: the same fields as above
         1. также см. scripts/create_index.sql
2. preact_front
   1. 
3. 
4. после всего выполнить:
   1. sh alembic.sh
   2. sh create_trigram.sh
