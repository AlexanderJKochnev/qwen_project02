# перенос данных mongo_db -> seaweed
1. ##  получениие словаря
       items.id: (image_id, title & subtitle)
2. ##  основной цикл
2.1. ###  получение изображения по image_id
2.2. ###  обработка и сохраненbе изображения + meta data (title & subtitle), получение fid
2.3. ###  сохранение fid -> items.seaweed_fids[0]
6. ##  переделать route /api/image/{id}, /api/thumbnail/{id}
7. ##  бесшовно переделать /mongodbb/get...
