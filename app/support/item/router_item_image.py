# app.support.items.router_item_image.py

# app.core.support.seaweeds.router.py
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
from app.core.enum import Alignment, COLORS
from app.core.utils.converters import color_converter
from app.core.utils.io_utils import get_dirpath, get_file_list, ResponseStreaming
from app.core.utils.pydantic_utils import get_service

"""

"""
ColorType = Literal[*COLORS.keys()]
fonts_dir = get_dirpath('fonts')
fonts_list = get_file_list(fonts_dir)
Fonts = Literal[*fonts_list]


class ItemImageRouter:
    def __init__(self):
        prefix = 'item_image'
        self.tags, self.prefix = [f'{prefix}'], f'/{prefix}'
        self.router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=[Depends(get_active_user_or_internal)]
        )
        self.setup_routes()

    def setup_routes(self):
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
        self.router.add_api_route(
            "/generator4/{id}", self.test_generate_by_id, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

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
        shadow_offset = (shadow_x, shadow_y)

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
            "font_path": font,
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
        shadow_offset = (shadow_x, shadow_y)

        result = {
            "width": width,
            "height": height,
            "font_path": font,
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

    async def test_generate_simple(self, request: Request, id: int = Path(..., description='id items - любое число'),
                                   fill_opacity: int = Query(default=50,
                                                             ge=0, le=255,
                                                             description="Прозрачность шрифта от 0 - полностью "
                                                                         "прозрачное до 255 - непрозрачное"),
                                   background_color: ColorType = Query('WHITE_WINE', description="Цвет фона"),
                                   shadow_x: int = Query(10, ge=-10, le=10,
                                                         description="Тень, смещение по оси X"),
                                   shadow_y: int = Query(10, ge=-10, le=10,
                                                         description="Тень, смещение по оси Y"),
                                   shadow_opacity: int = Query(100,
                                                               ge=0, le=255,
                                                               description="Прозрачность тени. Желательно меньше "
                                                                           "прозрачности шрифта. Но при полностью "
                                                                           "прозрачном шрифте и непрозрачной тени "
                                                                           "тоже интересно"
                                                                           " "),
                                   font: Fonts = Query(..., description='шрифт'),
                                   session: AsyncSession = Depends(get_db)
                                   ):
        """
            Генерaция изображения из названия напитка
        """
        if shadow_x != 0 or shadow_y != 0:
            shadow_offset = (shadow_x, shadow_y)
        else:
            shadow_offset = None, None

        result = {
            "width": 380,
            "height": 500,
            "font_path": font,
            "initial_font_size": 85,
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

    async def test_generate_by_id(self, request: Request,
                                  id: int = Path(..., description='id items - любое число'),
                                  font: Fonts = Query(..., description='шрифт'),
                                  session: AsyncSession = Depends(get_db)
                                  ):
        """
            Генерaция изображения из названия напитка
        """
        print(f'{fonts_list=}')
        service = get_service('Item')
        response: bytes = await service.test_generate_by_id(request, id, font, session)
        # return response
        return ResponseStreaming(response)
