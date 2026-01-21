## Добавление языков;
1. app.core
   1. ap.core.models
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
   3. 