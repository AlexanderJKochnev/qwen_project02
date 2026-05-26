# app.core.support.seaweeds.router.py
from typing import List, Literal
from app.core.enum import Alignment, COLORS
from fastapi import File, HTTPException, Path, Query, UploadFile, BackgroundTasks, Request
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.utils.converters import color_converter
from app.core.utils.io_utils import get_dirpath, get_file_list, ResponseJust, ResponseStreaming
from app.core.config.database.db_async import get_db
from app.auth.dependencies import get_active_user_or_internal
from app.core.services.seaweed_service import SeaweedsService
from app.core.utils.pydantic_utils import get_service
from app.mongodb.service import ThumbnailImageService


"""
    all bellow routes for the test purpose only
    create
    search
    get
    get_by_id
    delete
    update
"""
ColorType = Literal[*COLORS.keys()]
fonts_dir = get_dirpath('fonts')
fonts_list = get_file_list(fonts_dir)
Fonts = Literal[*fonts_list]


class SeaweedsRouter:
    def __init__(self):
        prefix = 'seaweeds'
        self.tags, self.prefix = [f'{prefix}'], f'/{prefix}'
        self.router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=[Depends(get_active_user_or_internal)]
        )
        # self.service: SeaweedsService = Depends()
        self.setup_routes()
        # super().__init__(prefix='/seaweeds')

    def setup_routes(self):
        self.router.add_api_route(
            "/search_fids", self.search_by_tag, methods=["GET"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/search_image", self.search_image_by_fid,
            methods=["GET"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.get, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/transfer", self.transfer_mongoo_sea,
            methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/{fid}", self.get_by_fid, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/direct/{fid}", self.get_direct_by_fid, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.create_img, methods=["POST"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/png_load", self.create_img2, methods=["POST"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "test", self.test_create_img, methods=["POST"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.delete_img, methods=["DELETE"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/thumb/{fid}",
            self.get_thumb, methods=["GET"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/thumb_image/{fid}", self.get_thumb_by_fid, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/generator/{id}", self.test_generate_image_by_text, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/generator2/{id}", self.test_generate_by_background, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/generator3/{id}", self.test_generate_simple, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

    async def create_img(self,
                         description: str = Query(..., description='ключевые слова по которым можно найти '
                                                  'изображение'),
                         table_name: str = Query('items', description='имя таблицы для которой '
                                                                      'предназначено изображение. items'),
                         content_type: int = Query(0, description='возвращает результат: 0 - ничего, '
                                                   '1 - полное изображение, 2 - thumbnail'),
                         processor_type: int = Query(4, description='выбор процессора'),
                         file: UploadFile = File(...),
                         service: SeaweedsService = Depends()):
        try:
            content = await file.read()
            # response: (meta, content | None)
            meta, content = await service.create_img2(content, description, table_name, content_type, processor_type)
            if content:
                kwargs = {key: val for key, val in meta.items() if key in ('fid', 'fid_thumb', 'tags')}
                if isinstance(content, list):
                    content = content[-1]
                return ResponseStreaming(content, **kwargs)
            else:
                return meta
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=e)

    async def create_img2(self,
                          description: str = Query(..., description='ключевые слова по которым можно найти '
                                                   'изображение'),
                          table_name: str = Query('items', description='имя таблицы для которой '
                                                  'предназначено изображение. items'),
                          content_type: int = Query(0, description='возвращает результат: 0 - ничего, '
                                                    '1 - полное изображение, 2 - thumbnail'),
                          file: UploadFile = File(...),
                          service: SeaweedsService = Depends()):
        """
            загрзука готовых png изображений с прозрачным фоном в базу данных:
            1. дедупликация (ищет нет ли уже похожего)
            3. создание thumbnail
            4. загрузка в базу данных
        """
        try:
            content = await file.read()
            # response: (meta, content | None)
            meta, content_bytes = await service.create_img_light(content, description, table_name, content_type)
            if content_bytes:
                logger.warning(f'{len(content_bytes)=}, {len(content)=}')
                kwargs = {key: val for key, val in meta.items() if key in ('fid', 'fid_thumb', 'tags')}
                if isinstance(content_bytes, list):
                    content_bytes = content[-1]
                return ResponseStreaming(content_bytes, **kwargs)
            else:
                return meta
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=e)

    async def delete_img(self, fid: str,
                         table_name: str = Query('items', description='имя таблицы для которой '
                                                 'предназначено изображение. items'
                                                 ),
                         service: SeaweedsService = Depends()) -> dict:
        """
            удаление изображения
        """
        await service.delete_img(fid, table_name)
        return {'fid': fid,
                'result': 'deleted'}

    async def get(self,
                  page: int = Query(1, description='страница'),
                  page_size: int = Query(1, description='размер страницы страница'),
                  # include_deleted: bool = Query(False, description='включить удаленные записи?'),
                  order_by: str = Query('inserted_at DESC', description='порядок сортировки '),
                  service: SeaweedsService = Depends()
                  ) -> dict:
        """
        получение списка  fid изображений по странично / только для тестирования
        """
        response = await service.get(page, page_size, order_by)
        return response

    async def get_by_fid(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение изображения по fid
        """
        image_data: bytes = await service.get_image(fid)
        return ResponseStreaming(image_data)
        # return StreamingResponse(**image_data)

    async def get_thumb_by_fid(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение thum изображения
        """
        image_data: bytes = await service.get_thumb_by_fid(fid)
        return ResponseStreaming(image_data)

    async def get_thumb(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение fid, fid_thumb by fid
        """
        response = await service.get_fid_thumb(fid)
        return response

    async def get_direct_by_fid(self, fid: str, service: SeaweedsService = Depends()) -> bytes:
        """
        получение изображения по fid напрямую из seaweed
        """
        image_data: bytes = await service.get_direct_image(fid)
        return ResponseJust(image_data)

    async def search_by_tag(self, tag_value: str, service: SeaweedsService = Depends()):
        """
        получение fid изображения по tag
        """
        result: List[dict] = await service.search_fid_by_tag(tag_value)
        return result
        # return StreamingResponse(**image_data)

    async def search_image_by_fid(self, tag_value: str,
                                  image_type: int = Query(1, description='1: полное изображениеб 2: thumbnail'),
                                  service: SeaweedsService = Depends()):
        """
        получение изображения по tag
        """
        image_data: bytes = await service.search_image_by_tag(tag_value, image_type)
        return ResponseStreaming(image_data)
        # return StreamingResponse(**image_data)

    async def transfer_mongoo_sea(self, batch: int, background_tasks: BackgroundTasks,
                                  session: AsyncSession = Depends(get_db),
                                  service: SeaweedsService = Depends(),
                                  image_service: ThumbnailImageService = Depends()):
        # перенос (копирование) файлов из mongodb в seaweed, запись fid в items.seaweed_fids[0]
        # запускать только один раз
        # response = await service.get_items_pairs(session, image_service)
        # запись в items.seaweed_fids[1] thumbnails fids
        # response = await service.transfer_tier2(session, image_service)
        # новый encoder webp
        response = await service.transfer_tier1(batch, background_tasks, session, image_service)
        return {'result': response}

    async def test_create_img(self,
                              file: UploadFile = File(...),
                              dimension: int = Query(1000,
                                                     description='максимальный размер в который нужно вписать '
                                                                 'изображение, pix'),
                              size: int = Query(100, description='максимальный размер файла, Kb'),
                              quality: int = Query(85, description='качество изображениия 100 самое лучшее, 0 плохое'),
                              type: int = Query(1,
                                                description='1. PNG, 2. WEBP OLD, 3. WEBP LOSSLESS, '
                                                            '4. WEBP LOSSY, 5. WEBP LOSSY BATCH'),
                              full: bool = Query(True, description='True полное, False thumbnail'),
                              service: SeaweedsService = Depends()):
        """
             загрузка обработка и возврат изображеня БЕЗ сохранения - для оценки качества обработки
        """
        from app.core.utils.hashes import FastImageHasher
        content = await file.read()
        source_hash = FastImageHasher.xxhash64(content)
        original_size = len(content)
        logger.info(f'{original_size=}')
        image_data = await service.test_create_img(content, dimension, size, type, quality, full)
        return ResponseStreaming(image_data, source_size=original_size, xxhash=source_hash)

    async def test_generate_image_by_text(self, request: Request, id: int = Path(..., description='id items'),
                                          width: int = Query(380, description="ширина холста"),
                                          height: int = Query(500, description="высота холста"),
                                          text_alignment: Alignment = Query("center", description="выравнивание "
                                          "текста"),
                                          initial_font_size: int = Query(
                                              85, description="размер шрифта, пробуй менять совместно с размером "
                                                              "холста"),
                                          padding: int = Query(10, ge=1, le=15, description="поля по краям"),
                                          stroke_width: int = Query(2, description="ширина оканттовки букв"),
                                          stroke_color: ColorType = Query("BLACK", description="Цвет окантовки"),
                                          fill_color: ColorType = Query("RED", description="Цвет шрифта"),
                                          fill_opacity: int = Query(default=0,
                                                                    ge=0, le=255,
                                                                    description="Прозрачность шрифта"),
                                          background_color: ColorType = Query('WHITE', description="Цвет фона"),
                                          bg_opacity: int = Query(0,
                                                                  ge=0, le=255,
                                                                  description="Прозрачность фона"),
                                          shadow_x: int = Query(0, ge=-10, le=10,
                                                                description="Тень, смещение по оси X"),
                                          shadow_y: int = Query(0, ge=-10, le=10,
                                                                description="Тень, смещение по оси Y"),
                                          shadow_color: ColorType = Query("GRAY", description="Цвет фона"),
                                          shadow_opacity: int = Query(0,
                                                                      ge=0, le=255,
                                                                      description="Прозрачность тени"),
                                          font: Fonts = Query(..., description='шрифт'),
                                          session: AsyncSession = Depends(get_db)
                                          ):
        """
            Генереция изображения из названия напитка
        """
        fill_color = color_converter(COLORS.get(fill_color), fill_opacity)  # RGBA
        background_color = color_converter(COLORS.get(background_color), bg_opacity)  # RGBA
        stroke_color = color_converter(COLORS.get(stroke_color), 255)
        shadow_color = color_converter(COLORS.get(shadow_color), shadow_opacity)
        if shadow_x != 0 or shadow_y != 0:
            shadow_offset = (shadow_x, shadow_y)
        else:
            shadow_offset, shadow_color = None, None
        """
        result = TextConfig(text='dump',  # заглушка - текст получим в service layer
                            width=width, height=height, font_path=f'{fonts_dir}/{font}',
                            initial_font_size=initial_font_size,
                            min_word_length=3,
                            background_color=background_color,
                            fill_color=fill_color,
                            stroke_color=stroke_color,
                            stroke_width=stroke_width,
                            shadow_offset=shadow_offset,
                            shadow_color=shadow_color,
                            shadow_opacity=shadow_opacity,
                            fill_opacity=fill_opacity,
                            text_alignment=text_alignment,
                            padding=padding
                            )
        """
        result = {
            "width": width,
            "height": height,
            "font_path": f'{fonts_dir}/{font}',
            "initial_font_size": initial_font_size,
            "min_word_length": 3,
            "background_color": background_color,
            "fill_color": fill_color,
            "stroke_color": stroke_color,
            "stroke_width": stroke_width,
            "shadow_offset": shadow_offset,
            "shadow_color": shadow_color,
            "shadow_opacity": shadow_opacity,
            "fill_opacity": fill_opacity,
            "text_alignment": text_alignment,
            "padding": padding
        }
        service = get_service('Item')
        response: bytes = await service.test_generate_image_by_text(request, id, result, session)
        return ResponseStreaming(response)

    async def test_generate_by_background(self, request: Request, id: int = Path(..., description='id items'),
                                          width: int = Query(380, description="ширина холста"),
                                          height: int = Query(500, description="высота холста"),
                                          text_alignment: Alignment = Query("center", description="выравнивание "
                                          "текста"),
                                          initial_font_size: int = Query(
                                              85, description="размер шрифта, пробуй менять совместно с размером "
                                                              "холста"),
                                          padding: int = Query(10, ge=1, le=15, description="поля по краям"),
                                          stroke_width: int = Query(2, description="ширина оканттовки букв"),
                                          # stroke_color: ColorType = Query("BLACK", description="Цвет окантовки"),
                                          # fill_color: ColorType = Query("RED", description="Цвет шрифта"),
                                          fill_opacity: int = Query(default=0,
                                                                    ge=0, le=255,
                                                                    description="Прозрачность шрифта"),
                                          background_color: ColorType = Query('WHITE', description="Цвет фона"),
                                          bg_opacity: int = Query(0,
                                                                  ge=0, le=255,
                                                                  description="Прозрачность фона"),
                                          shadow_x: int = Query(0, ge=-10, le=10,
                                                                description="Тень, смещение по оси X"),
                                          shadow_y: int = Query(0, ge=-10, le=10,
                                                                description="Тень, смещение по оси Y"),
                                          # shadow_color: ColorType = Query("GRAY", description="Цвет фона"),
                                          shadow_opacity: int = Query(0,
                                                                      ge=0, le=255,
                                                                      description="Прозрачность тени"),
                                          font: Fonts = Query(..., description='шрифт'),
                                          session: AsyncSession = Depends(get_db)
                                          ):
        """
            Генереция изображения из названия напитка
        """
        if shadow_x != 0 or shadow_y != 0:
            shadow_offset = (shadow_x, shadow_y)
        else:
            shadow_offset = None, None

        result = {
            "width": width,
            "height": height,
            "font_path": f'{fonts_dir}/{font}',
            "initial_font_size": initial_font_size,
            "min_word_length": 3,
            "background_color": COLORS.get(background_color),
            # "fill_color": fill_color,
            # "stroke_color": stroke_color,
            "stroke_width": stroke_width,
            "shadow_offset": shadow_offset,
            # "shadow_color": shadow_color,
            "shadow_opacity": shadow_opacity,
            "fill_opacity": fill_opacity,
            "text_alignment": text_alignment,
            "padding": padding
        }
        service = get_service('Item')
        response: bytes = await service.test_generate_image_by_background(request, id, result, session)
        return ResponseStreaming(response)

    async def test_generate_simple(self, request: Request, id: int = Path(..., description='id items'),
                                   fill_opacity: int = Query(default=0,
                                                             ge=0, le=255,
                                                             description="Прозрачность шрифта"),
                                   background_color: ColorType = Query('WHITE', description="Цвет фона"),
                                   shadow_x: int = Query(10, ge=-10, le=10,
                                                         description="Тень, смещение по оси X"),
                                   shadow_y: int = Query(10, ge=-10, le=10,
                                                         description="Тень, смещение по оси Y"),
                                   shadow_opacity: int = Query(0,
                                                               ge=0, le=255,
                                                               description="Прозрачность тени"),
                                   font: Fonts = Query(..., description='шрифт'),
                                   session: AsyncSession = Depends(get_db)
                                   ):
        """
            Генереция изображения из названия напитка
        """
        if shadow_x != 0 or shadow_y != 0:
            shadow_offset = (shadow_x, shadow_y)
        else:
            shadow_offset = None, None

        result = {
            "width": 500,
            "height": 800,
            "font_path": f'{fonts_dir}/{font}',
            "initial_font_size": 80,
            "min_word_length": 3,
            "background_color": COLORS.get(background_color),
            # "fill_color": fill_color,
            # "stroke_color": stroke_color,
            "stroke_width": 1,
            "shadow_offset": shadow_offset,
            # "shadow_color": shadow_color,
            "shadow_opacity": shadow_opacity,
            "fill_opacity": fill_opacity,
            "text_alignment": 'center',
            "padding": 10
        }
        service = get_service('Item')
        response: bytes = await service.test_generate_image_by_background(request, id, result, session)
        return ResponseStreaming(response)
