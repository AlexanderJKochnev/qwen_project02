## Добавление языков - испрользовать строго двухзначный код языка согласно стандарту ISO 639-1;
### перевод будет осуществляться автоматически при редактировании если язык указан согласно стандарту ISO 639-1
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
      3. app/support/item/schemas/
           # class ItemApi(ItemApiRoot)
2. preact_front
   1. src/pages/HandbookUpdateForm.tsx
      # const [formData, setFormData] = useState({
        # name_xx: '',
        # description_xx: '',
      # setFormData({
        # name_xx: data.name_xx || '',
        # description_xx: data.description_xx || '',
      # /* 
              <div>
                <label className="label">
                  <span className="label-text">Name (French)</span>
                </label>
                <input
                  type="text"
                  name="name_fr"
                  value={formData.name_fr}
                  onInput={handleChange}
                  className="input input-bordered w-full"
                  placeholder="Nom en Francais"
                />
              </div>
      # /*
              <div>
                <label className="label">
                  <span className="label-text">Description (Xxxx)</span>
                </label>
                <textarea
                  name="description_xx"
                  value={formData.description_xx}
                  onInput={handleChange}
                  className="textarea textarea-bordered w-full"
                  rows={3}
                  placeholder="Description en Francais"
                />
              </div>
              */

   2. src/pages/HandbookUpdateForm.tsx
        # const [formData, setFormData] = useState({
        # то же самое как и в HandbookUpdateForm - просто скопируй между {/**/} 2 раза для name & description
   3. src/pages/ItemUpdateForm.tsx (поиск по {/* lang )
        # const [formData, setFormData] = useState({
        # 
3. 
4. после всего выполнить:
   1. sh alembic.sh
   2. sh create_trigram.sh
