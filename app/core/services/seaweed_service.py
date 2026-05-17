# app.support.seaweeds.service.py
"""
    СЕРВИСНЫЙ СЛОЙ ДЛЯ SEAWEEDFS
    вместо seaweed.filer используем clickhouse
    поэтому на этом слое объединяются обе базы данных
    seaweed: хранение и отдача по fid
    clickhouse: каталог в таблице images_metadata, поиск по тегам
    (в таблице images_metadata нет своего id только fid)
    create
    search
    get
    get_by_id
    delete
    update

"""
import aiohttp
from fastapi import Depends
from aiohttp.client_exceptions import ClientResponseError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.base_model import get_model_by_name
from app.core.utils.common_utils import get_random_string
from app.core.utils.image_utils import image_aligning
from app.core.config.database.seaweed_async import SeaweedFSManager, get_swfs
from app.core.config.project_config import settings
# from app.core.hash_norm import tokenize
from app.core.repositories.seaweed_repository import SeaweedRepository
from app.core.utils.image_webp import detect_image_format_fast, process_image_to_webp
from app.core.utils.pydantic_utils import get_repo
from app.dependencies import ClickHouseRepositoryFactory, get_clickhouse_repository_factory
from loguru import logger  # NOQA: F401
from app.mongodb.service import ThumbnailImageService


class SeaweedsService:
    def __init__(self, fs: SeaweedFSManager = Depends(get_swfs),
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.fs = fs
        self.click_repo = click_repo_factory.for_table('images_metadata')
        self.seaweed_repo = SeaweedRepository

    async def create_img(self, content: bytes, description: str, table: str) -> dict:
        """
            content: изображение в байтах
            description: описание
            table: для какой таблицы ?
            сохранение изображения:
            1. обработка (удаление фона, уменьшение размера, создание thumbnail, получение метаданных)
            2. обработка метаданных (токенизация по шаблону clickhouse, )
            3. сохранение 2-х файлов в seaweed, получение 2-х FID
            4. сохранение метаданных в clickhouse (fid thumbnail и full fid в одной записи)
            5. возврат fid
        """
        # from app.core.utils.common_utils import jprint
        # 1. обработка (удаление фона, уменьшение размера, создание thumbnail, получение метаданных)
        # full_data, thumb_data, meta_data = image_aligning(content)
        full_data, thumb_data, meta_data = process_image_to_webp(
            content=content, remove_bg=True, max_size_kb=100, thumb_size=150
        )
        # 2. обработка метаданных (токенизация по шаблону clickhouse, )
        ipts: dict = meta_data.get('iptc')
        tmp = ''
        if ipts:    # метаданные в файле
            tmp = ' '.join((f'{val}' for val in ipts.values() if val))
        tags = f'{tmp} {description}'   # tags теперь string - нормализовать не нужно - это делает индекс click
        meta: dict = {}
        """
         metadata.update(
            {'full_size_bytes': len(full_data),
             'thumb_size_bytes': len(thumb_data),
             'full_mime': 'image/webp',
             'thumb_mime': 'image/webp'}
        """
        meta['table'] = table
        # meta['uploaded_at'] = datetime.now(timezone.utc)
        meta['size_bytes'] = meta_data.get('full_size_bytes')
        meta['mime_type'] = meta_data.get('full_mime_type')
        meta['thumb_size_bytes'] = meta_data.get('thumb_size_bytes')
        meta['tags'] = tags
        # 3. сохранение 2-х файлов в seaweed, получение 2-х FID
        fid = await self.fs.upload(full_data)
        fid_thumb = await self.fs.upload(thumb_data)
        # 4. сохранение метаданных в clickhouse (fid thumbnail и full fid в одной записи)
        meta['fid'] = fid
        meta['fid_thumb'] = fid_thumb
        # jprint(meta)
        await self.click_repo.create(meta)
        # 5. результат {fid: str, url: str}
        result = meta
        # result = {"fid": fid, "fid_thumb": fid_thumb, }
        return result

    async def delete_img(self, fid: str, table: str):
        """
        удаление изображения
        1. поиск в clickhouse by fid
        2. получение fid_thumb
        3. удаление 2-х записей из seaweed
        4. удаление fid seaweed
        """
        # 1. поиск в clickhouse by fid
        response: dict = await self.click_repo.get_by_id('fid', fid)
        if not response:
            raise ClientResponseError(status=400, message=f"Record with id '{fid}' not Found")
        logger.warning(f'1==={response=}')
        # 2. получение fid_thumb
        fid_thumb = response.get('fid_thumb')
        # 3. удаление 2-х записей из seaweed
        try:
            await self.fs.delete(fid)
        except ClientResponseError as e:
            if e.status != 404:  # если 404 значит нужно продолжать удалдениие в click
                raise e
        try:
            await self.fs.delete(fid_thumb)
        except ClientResponseError as e:
            if e.status != 404:  # если 404 значит нужно продолжать удалдениие в click
                raise e
        # 4. удаление fid seaweed
        await self.click_repo.soft_delete('fid', fid, table)
        return True

    async def get(self, page: int = 1, page_size: int = 20,
                  order_by: str = None) -> dict:
        """
        получение списка изображений
        """
        response = await self.click_repo.get(order_by=order_by,
                                             limit=page_size,
                                             page=page,
                                             fields=('fid', 'fid_thumb'))
        fids = [{v.get('fid'): v.get('fid_thumb')} for v in response]
        result = {'page': page,
                  'page_size': page_size,
                  'items': fids
                  }
        return result

    async def get_thumbnail_id(self, fid: str) -> str:
        """
            получение thumbnail: url_thumbnail
        """
        result = await self.click_repo.get_by_id('fid', fid)
        return result.get('fid_thumb')

    async def get_image(self, fid: str) -> dict:
        """
            получение изображения по fid (любого)
        """
        content = await self.seaweed_repo.get_by_fid(fid, self.fs)
        mime_type, ext = detect_image_format_fast(content)
        file_name = f'{get_random_string(8)}.{ext}'
        headers = {"Content-Disposition": f"inline; filename={file_name}", "X-Image-Type": "none",
                   "X-File-Size": str(len(content))}
        result = {'content': content,
                  'media_type': mime_type,
                  'headers': headers,
                  'status_code': 200,
                  "Content-Disposition": f"inline; filename={file_name}",
                  "X-Image-Type": "none",
                  "X-File-Size": str(len(content))
                  }
        return result

    async def get_direct_image(self, fid: str) -> dict:
        """
            получение изображения по fid (любого)
        """
        image_url = settings.seaweed_url
        async with aiohttp.ClientSession() as client:
            content = await client.get(image_url)
        content = await self.seaweed_repo.get_by_fid(fid, self.fs)
        file_name = f'{get_random_string(8)}.png'
        headers = {"Content-Disposition": f"inline; filename={file_name}", "X-Image-Type": "none",
                   "X-File-Size": str(len(content))}
        result = {'content': content,
                  'media_type': 'image/png',
                  'headers': headers,
                  'status_code': 200,
                  "Content-Disposition": f"inline; filename={file_name}",
                  "X-Image-Type": "none",
                  "X-File-Size": str(len(content))
                  }
        return result

    async def get_fid_thumb(self, fid: str) -> dict:
        """
            получение fid_thumb by fid
            {
                "fid": "4,08f358d709",
                "fid_thumb": "1,09f5d17a2b"
            }
        """
        result: dict = await self.click_repo.get_by_id('fid', fid, ['fid', 'fid_thumb'])
        return result

    async def get_fids_thumb(self, fids: list) -> dict:
        """
            получение список fid_thumb by списко fids
            [{
                "fid": "4,08f358d709",
                "fid_thumb": "1,09f5d17a2b"
            }, ...]
        """
        result: dict = await self.click_repo.get_by_ids('fid', fids, ['fid', 'fid_thumb'])
        return result

    async def get_thumb_by_fid(self, fid: str) -> dict:
        """
        получение thumbnail
        """
        # 1. получение fid_thumb
        result: dict = await self.click_repo.get_by_id('fid', fid, ['fid', 'fid_thumb'])
        fid_thumb = result.get('fid_thumb')
        # 2. получение изображения
        result = await self.get_image(fid_thumb)
        return result

    async def search_fid_by_tag(self, tag_value: str) -> dict:
        """
            поиск по тэгу. возвращает пару {fid: fid_thumbnail}
        """
        # 1. получение fid: fid_thumb
        result: dict = await self.click_repo.exact_search(tag_value)
        return result

    async def search_image_by_tag(self, tag_value: str, image_type: int):
        """
            поиск изображеня по тегу
            возвращает 1 - полное изображение
                        2 thumbnail
        """
        fids: dict = await self.search_fid_by_tag(tag_value)
        if fids:
            if image_type == 1:
                fid = fids.get('fid')
            else:
                fid = fids.get('fid_thumb')
        result = await self.get_image(fid)
        return result

    async def get_items_pairs(self, session: AsyncSession, image_service: ThumbnailImageService):
        """
            перенос mongodb -> seaweed
            запускать только ОДИН РАЗ
        """
        # 0. получение списка из items
        repository = get_repo('Item')
        model = get_model_by_name('Item')
        response = await repository.get_item_drink(session)
        cycle = ((a.id, a.image_id, a.concat) for a in response)
        result: dict = {}
        for id, image_id, description in cycle:
            #  print(f'{id=}, {image_id=}, {context=}')
            """
                {"content": image_data["content"],
                 "filename": image_data["filename"],
                 "content_type": image_data.get("content_type", "image/png"),
                 "from_cache": False}
            """
            # 1. получениие полного изображения из mongodb
            image_dict = await image_service.get_full_image(image_id)
            content: bytes = image_dict["content"]
            # 2. обработка и загрузка полученного изображения
            res: dict = await self.create_img(content, description, 'items')
            # 3. запись fid в Items.seaweed_fids[0]
            fid_list = [res.get('fid')]
            response = await repository.add_to_array(id, fid_list, model, 'seaweed_fids', session)
            result[id] = response
        return result

    async def transfer_tier2(self, session: AsyncSession, image_service: ThumbnailImageService):
        # 0. получение списка из items
        result: dict = {}
        repository = get_repo('Item')
        model = get_model_by_name('Item')
        response = await repository.get_item_drink2(session)
        if not response:
            return result
        # 0.1. список fids
        fids = [a.seaweed_fids for a in response]
        # 1. получение списка thunmbnails & fids
        thumbs: dict = await self.get_fids_thumb(fids)
        cycle = ((a.id, a.seaweed_fids, ) for a in response)
        result: dict = {}
        for id, fid in cycle:
            if thumb := thumbs.get(fid):
                res = await repository.replace_by_index_array(id, 1, thumb, model, 'seaweed_fids', session)
                result[id] = res
        return result
