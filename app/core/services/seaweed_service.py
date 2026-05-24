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
from typing import List

import aiohttp
from fastapi import Depends, HTTPException, BackgroundTasks
from aiohttp.client_exceptions import ClientResponseError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import DatabaseManager
from app.core.models.base_model import get_model_by_name
from app.core.utils.common_utils import jprint  # noqa: F401
from app.core.utils.hashes import FastImageHasher
from app.core.config.database.seaweed_async import SeaweedFSManager, get_swfs
from app.core.config.project_config import settings
from app.core.repositories.seaweed_repository import SeaweedRepository
from app.core.utils.headers import make_meta
# from app.core.utils.headers import generate_image_headers
from app.core.utils.image_processor import ImageProcessingConfig, ImageProcessor
from app.core.utils.image_utils import image_aligning
from app.core.utils.image_webp import process_image_to_webp
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

    async def hash_exists(self, source_hash: int) -> tuple:
        """
            проверка - существует ли уже изображение если до возвращает fis fid_thumb
        """
        res: dict = await self.click_repo.get_by_id(
            'data_hash', source_hash, ['fid', 'fid_thumb', 'tags']
        )
        if res:  # изображение с этим хэшем уже есть - просто возвращаем его без создания нового
            fid, fid_thumb, tags = res.values()
            return fid, fid_thumb
        return None

    async def image_processing(self, content, type: int):
        """ обработка изображения разными способами """
        dim, size, quality = settings.MAX_FULL_HEIGHT, settings.MAX_FILE_SIZE, settings.WEBP_QUALITY
        match type:
            case 1:  # PNG
                # full_data, thumb_data, meta_data
                return image_aligning(content, True, dim, size, quality)
            case 2:  # OLD WEBP
                return process_image_to_webp(
                    content=content, remove_bg=True,
                    max_size_kb=settings.MAX_FILE_SIZE, thumb_size=settings.MAX_THUMB_WIDTH,
                    dim=settings.MAX_FULL_HEIGHT,
                    quality=settings.WEBP_QUALITY
                )
            case 3:  # WEBP LOSSLESS
                config_deterministic = ImageProcessingConfig(
                    max_full_width=dim, max_full_height=1024, max_thumb_width=200, max_thumb_height=200,
                    webp_lossless=True, deterministic_mode=True,  # Включаем детерминизм
                    rembg_seed=42, rembg_num_threads_deterministic=1, rembg_model="u2net"
                )
                processor_det = ImageProcessor(config_deterministic)
                return await processor_det.process_single(content, remove_bg=True)
            case 4:  # WEBP LOSSY
                config_fast = ImageProcessingConfig(
                    max_full_width=dim, max_full_height=dim, max_thumb_width=200, max_thumb_height=200,
                    webp_lossless=False,  # Lossy для скорости и размера
                    webp_quality=quality, deterministic_mode=False,  # Отключаем детерминизм
                    rembg_num_threads_fast=4, rembg_model="u2net"
                )
                processor_fast = ImageProcessor(config_fast)
                return await processor_fast.process_single(content, remove_bg=True)
            case 5:  # WEBP LOSSY BATCH
                config_fast = ImageProcessingConfig(**settings.imageprocessing_config)
                processor_fast = ImageProcessor(config_fast)
                contents = [content] * 10
                result = await processor_fast.process_batch(contents, remove_bg=True)
                # compaire results
                return result[-1]
            case _:  # WEBP LOSSY
                config_fast = ImageProcessingConfig(**settings.imageprocessing_config)
                processor_fast = ImageProcessor(config_fast)
                return await processor_fast.process_single(content, remove_bg=True)

    async def create_img2(self, content: bytes, description: str, table: str,
                          content_include: int = 0, processor_type: int = 4,
                          ) -> dict | tuple:
        """
        ntcn
        """
        # 0. get hash
        source_hash = FastImageHasher.xxhash64(content)
        # 1. find by hash
        res: dict = await self.click_repo.get_by_id('data_hash', source_hash,
                                                    ['fid', 'fid_thumb', 'tags'])
        if res:     # изображение с этим хэшем уже есть - просто возвращаем его без создания нового
            fid, fid_thumb, tags = res.values()
            if content_include == 1:
                content_data: bytes = await self.seaweed_repo.get_by_fid(fid, self.fs)
            elif content_include == 2:
                content_data: bytes = await self.seaweed_repo.get_by_fid(fid_thumb, self.fs)
            else:
                content_data = None
            return {'tags': tags, 'fid': fid, 'fid_thumb': fid_thumb}, content_data
        # 2. загруженное изображение новое - обрабатываем
        result = await self.image_processing(content, processor_type)
        if result:
            full_data, thumb_data, meta_data = result
            # 3. save to seaweed
            fid = await self.fs.upload(full_data)
            fid_thumb = await self.fs.upload(thumb_data)
            # 4. save to clickhouse
            # 4.1. meta data generation
            meta = make_meta(
                fid, fid_thumb, full_data, thumb_data,
                description, source_hash, table, meta_data.get('full_mime_type')
            )
            logger.warning(f'{meta=}')
            # 4.2. saving
            await self.click_repo.create(meta)
        # возврат результата
        match content_include:
            case 0:
                result = {'test': source_hash}, None
            case 1:
                result = {'test': source_hash}, full_data
            case _:
                result = {'test': source_hash}, thumb_data
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
            raise HTTPException(status_code=404, detail=f"Record with id '{fid}' not Found")
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

    async def get_image(self, fid: str) -> bytes:
        """
            получение изображения по fid (любого)
        """
        content: bytes = await self.seaweed_repo.get_by_fid(fid, self.fs)
        return content

    async def get_direct_image(self, fid: str) -> bytes:
        """
            получение изображения по fid (любого)
        """
        image_url = f'{settings.seaweed_url}/{fid}'
        logger.info(f'{image_url=}')
        async with aiohttp.ClientSession() as client:
            async with client.get(image_url) as response:
                content: bytes = await response.read()
        return content

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

    async def get_thumb_by_fid(self, fid: str) -> bytes:
        """
        получение thumbnail
        """
        # 1. получение fid_thumb
        result: dict = await self.click_repo.get_by_id('fid', fid, ['fid', 'fid_thumb'])
        fid_thumb = result.get('fid_thumb')
        # 2. получение изображения
        result: bytes = await self.get_image(fid_thumb)
        return result

    async def search_fid_by_tag(self, tag_value: str) -> List[dict]:
        """
            поиск по тэгу. возвращает пару {fid: fid_thumbnail}
        """
        # 1. получение fid: fid_thumb
        result: List[dict] = await self.click_repo.exact_search(tag_value)
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

    async def transfer_tierX(self, batch: int, background_tasks: BackgroundTasks, session: AsyncSession,
                             image_service: ThumbnailImageService):
        """
            перенос mongodb -> seaweed
            запускать только ОДИН РАЗ
        """
        # 0. объявляем переменные
        repository = get_repo('Item')
        model = get_model_by_name('Item')
        result: dict = {}
        contents: dict = {}
        # 1. получение списка из items
        response = await repository.get_item_drink(session)
        if not response:
            return None
        for id, image_id, description in ((a.id, a.image_id, a.concat) for a in response):
            # 1. получениие полного изображения из mongodb
            image_dict = await image_service.get_full_image(image_id)
            content: bytes = image_dict["content"]
            # 0. get hash
            source_hash = FastImageHasher.xxhash64(content)
            # 1. find by hash
            res = await self.hash_exists(source_hash)
            if res:  # изображение с этим хэшем уже есть - просто возвращаем его без создания нового
                result['id'] = res
            # 2. изображение новое - копим
            contents[id] = (content, source_hash)
            # 3. накопили - обработка
            if len(contents) >= batch:
                pass
            res: dict = await self.create_img(content, description, 'items')
            # 3. запись fid в Items.seaweed_fids[0]
            fid_list = [res.get('fid')]
            response = await repository.add_to_array(id, fid_list, model, 'seaweed_fids', session)
            result[id] = response
        return result

    async def transfer_tier2(self, session: AsyncSession, image_service: ThumbnailImageService):
        # запись thumbnails seaweed_fids
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

    async def transfer_tier3(self, session: AsyncSession, image_service: ThumbnailImageService):
        # запись thumbnails seaweed_fids
        result: dict = {}
        repository = get_repo('Item')
        model = get_model_by_name('Item')
        response = await repository.get_item_drink3(session)
        if not response:
            return result
        cycle = ((a.id, a.image_id, a.concat) for a in response)
        result: dict = {}
        for id, image_id, description in cycle:
            image_dict = await image_service.get_full_image(image_id)
            content: bytes = image_dict["content"]
            res: dict = await self.create_img(content, description, 'items')
            # 3. запись fid в Items.seaweed_fids[0]
            fid_list = [res.get('fid'), res.get('fid_thumb')]
            response = await repository.add_to_array(id, fid_list, model, 'seaweed_fids', session)
            logger.success(f'создано: {response}')
            result[id] = response
        return result

    async def test_create_img(self, content: bytes, dim: int, size: int, type: int, quality: int, fu: bool) -> bytes:
        """
            content: изображение в байтах
        """
        # 1. обработка (удаление фона, уменьшение размера, создание thumbnail, получение метаданных)
        source_hash = FastImageHasher.xxhash64(content)
        logger.warning(f'{source_hash=}')
        match type:
            case 1:  # PNG
                full_data, thumb_data, meta_data = image_aligning(content, True, dim, size, quality)
            case 2:  # OLD WEBP
                full_data, thumb_data, meta_data = process_image_to_webp(
                    content=content, remove_bg=True, max_size_kb=size, thumb_size=20, dim=dim, quality=quality
                )
            case 3:  # WEBP LOSSLESS
                config_deterministic = ImageProcessingConfig(
                    max_full_width=dim, max_full_height=1024, max_thumb_width=200, max_thumb_height=200,
                    webp_lossless=True, deterministic_mode=True,  # Включаем детерминизм
                    rembg_seed=42, rembg_num_threads_deterministic=1, rembg_model="u2net"
                )
                processor_det = ImageProcessor(config_deterministic)
                full_data, thumb_data, meta_data = await processor_det.process_single(content, remove_bg=True)
            case 4:  # WEBP LOSSY
                config_fast = ImageProcessingConfig(
                    max_full_width=dim, max_full_height=dim, max_thumb_width=200, max_thumb_height=200,
                    webp_lossless=False,  # Lossy для скорости и размера
                    webp_quality=quality, deterministic_mode=False,  # Отключаем детерминизм
                    rembg_num_threads_fast=4, rembg_model="u2net"
                )
                processor_fast = ImageProcessor(config_fast)
                full_data, thumb_data, meta_data = await processor_fast.process_single(content, remove_bg=True)
            case 5:  # WEBP LOSSY BATCH
                config_fast = ImageProcessingConfig(**settings.imageprocessing_config)
                """"
                config_fast = ImageProcessingConfig(
                    max_full_width=dim, max_full_height=dim, max_thumb_width=200, max_thumb_height=200,
                    webp_lossless=False,  # Lossy для скорости и размера
                    webp_quality=quality, deterministic_mode=False,  # Отключаем детерминизм
                    rembg_num_threads_fast=4, rembg_model="u2net"
                )
                """
                processor_fast = ImageProcessor(config_fast)
                contents = [content] * 10
                # full_data, thumb_data, meta_data
                result = await processor_fast.process_batch(contents, remove_bg=True)
                # compaire results
                # xxh = FastImageHasher.xxhash64
                # tmp = [(xxh(fd), xxh(td), len(fd), len(td)) for fd, td, meta in result]
                # jprint(tmp)
                logger.warning('-------------------------')
                full_data, thumb_data, meta_data = result[-1]
            case _:  # WEBP LOSSY
                config_fast = ImageProcessingConfig(**settings.imageprocessing_config)
                processor_fast = ImageProcessor(config_fast)
                full_data, thumb_data, meta_data = await processor_fast.process_single(content, remove_bg=True)
        if fu:
            content: bytes = full_data
        else:
            content: bytes = thumb_data
        return content

    async def transfer_tier1(self, batch: int, background_tasks: BackgroundTasks, session: AsyncSession,
                             image_service: ThumbnailImageService
                             ):
        """ IMPORT IMAGES FROM MONGO TO SEAWEED IN BACKGROUND """
        repository = get_repo('Item')
        model = get_model_by_name('Item')
        await repository.run_mongo_to_seaweed(
            repository=repository, model=model,
            image_service=image_service,
            click_repo=self.click_repo,
            fs=self.fs,
            session_factory=DatabaseManager.session_maker,
            background_tasks=background_tasks
        )
        logger.warning("background_tasks.add_task: status: ok")
        return "background_tasks.add_task: status: ok"
