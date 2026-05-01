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
from fastapi import Depends
from app.core.utils.common_utils import get_random_string
from app.core.utils.image_utils import image_aligning
from app.core.config.database.seaweed_async import SeaweedFSManager, get_swfs
from app.core.hash_norm import tokenize
from app.core.repositories.seaweed_repository import SeaweedRepository
from app.dependencies import ClickHouseRepositoryFactory, get_clickhouse_repository_factory
from loguru import logger  # NOQA: F401


class SeaweedsService:
    def __init__(self, fs: SeaweedFSManager = Depends(get_swfs),
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.fs = fs
        self.click_repo = click_repo_factory.for_table('images_metadata')
        # logger.warning(f"DEBUG: repo.client type = {type(self.click_repo.client)}")  # Должно быть AsyncClient
        self.seaweed_repo = SeaweedRepository

    async def create_img(self, content: bytes, description: str, table: str) -> dict:
        """
            сохранение изображения:
            1. обработка (удаление фона, уменьшение размера, создание thumbnail, получение метаданных)
            2. обработка метаданных (токенизация по шаблону clickhouse, )
            3. сохранение 2-х файлов в seaweed, получение 2-х FID
            4. сохранение метаданных в clickhouse (fid thumbnail и full fid в одной записи)
            5. возврат fid
        """
        from app.core.utils.common_utils import jprint
        # 1. обработка (удаление фона, уменьшение размера, создание thumbnail, получение метаданных)
        full_data, thumb_data, meta_data = image_aligning(content)

        # 2. обработка метаданных (токенизация по шаблону clickhouse, )
        ipts: dict = meta_data.get('iptc')
        tmp = ''
        if ipts:
            tmp = ' '.join((f'{val}' for val in ipts.values() if val))
        tags = tokenize(f'{tmp} {description}')
        meta: dict = {}
        meta['table'] = table
        # meta['uploaded_at'] = datetime.now(timezone.utc)
        meta['size_bytes'] = meta_data['size_bytes']
        meta['mime_type'] = meta_data['mime_type']
        meta['thumb_size_bytes'] = meta_data['thumbnail_size_bytes']
        meta['tags'] = tags
        jprint(meta)
        logger.warning(f'{type(full_data)=}')
        # 3. сохранение 2-х файлов в seaweed, получение 2-х FID
        fid = await self.fs.upload(full_data)
        logger.warning(f'{fid=}')
        logger.warning(f'{type(thumb_data)=}')
        fid_thumb = await self.fs.upload(thumb_data)
        logger.warning(f'{fid_thumb=}')
        # 4. сохранение метаданных в clickhouse (fid thumbnail и full fid в одной записи)
        meta['fid'] = fid
        meta['fid_thumb'] = fid_thumb
        jprint(meta)
        await self.click_repo.create(meta)
        # 5. результат {fid: str, url: str}
        result = {"fid": fid, "fir_thumb": fid_thumb}
        return result

    async def delete_img(self, fid):
        """
        удаление изображения
        1. поиск в clickhouse by fid
        2. получение fid_thumb
        3. удаление 2-х записей из seaweed
        4. удаление fid seaweed
        """
        # 1. поиск в clickhouse by fid
        response: dict = await self.click_repo.get_by_id('fid', fid)
        # 2. получение fid_thumb
        fid_thumb = response.get('fid_thumb')
        # 3. удаление 2-х записей из seaweed
        await self.fs.delete(fid)
        await self.fs.delete(fid_thumb)
        # 4. удаление fid seaweed
        await self.click_repo.soft_delete('fid', fid)

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
        file_name = f'{get_random_string(8)}.png'
        headers = {"Content-Disposition": f"inline; filename={file_name}", "X-Image-Type": "none",
                   "X-File-Size": str(len(content))}
        result = {'content': content,
                  'media-type': 'image/png',
                  'headers': headers,
                  'status_code': 200}
        return result

    async def get_fid_thumb(self, fid: str) -> tuple:
        """
             получение fid_thumb by fid
        """
        result = await self.click_repo.get_by_id('fid', fid, ['fid', 'fid_thumb'])
        return result
