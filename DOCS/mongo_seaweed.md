# перенос данных mongo_db -> seaweed
1. ##  основной цикл получениие словаря
       items.id: (image_id, title & subtitle)
2. ##  получение изображения по image_id
3. ##  обработка и сохраненbе изображения + meta data (title & subtitle), получение fid
4. ##  сохранение fid -> items.seaweed_fids[0]
5. ##  переделать route /api/image/{id}, /api/thumbnail/{id}
6. ##  бесшовно переделать /mongodbb/get...
