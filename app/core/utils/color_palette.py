import colorsys
from typing import Tuple
from PIL import ImageColor
from dataclasses import dataclass
from loguru import logger


@dataclass
class GeneratedPalette:
    """Результат автоматического подбора цветов."""
    fill_color: Tuple[int, int, int, int]
    stroke_color: Tuple[int, int, int, int]
    shadow_color: Tuple[int, int, int, int]


def auto_match_colors(background_color_str: str) -> GeneratedPalette:
    """
    Анализирует цвет фона и автоматически подбирает гармоничную,
    контрастную палитру для текста (тело, контур, тень).

    :param background_color_str: Цвет в любом формате Pillow ("#ff0000", "rgb(255,0,0)", "navy")
    """
    # 1. Парсим цвет фона в стандартный RGB (0-255)
    bg_rgb = ImageColor.getrgb(background_color_str)[:3]
    r, g, b = bg_rgb

    # 2. Переводим в формат HSV (от 0.0 до 1.0) для удобной работы с цветовым кругом
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

    # 3. Определяем яркость фона по формуле YIQ (восприятие глазом человека)
    # Формула дает вес каждому каналу: зеленый кажется нам самым ярким, синий — самым темным
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    is_dark_bg = brightness < 128  # True, если фон темный

    logger.debug(
        f"Анализ фона '{background_color_str}': Яркость={brightness:.1f} ({'Темный' if is_dark_bg else 'Светлый'}), H={h:.2f}, S={s:.2f}, V={v:.2f}"
    )

    # 4. Логика подбора цветов на основе гармонии
    if is_dark_bg:
        # --- НА ТЕМНОМ ФОНЕ ---
        # Тело букв: делаем максимально светлым (белым или очень легким оттенком фона)
        fill_rgb = colorsys.hsv_to_rgb(h, s * 0.1, 0.98)
        fill_color = (int(fill_rgb[0] * 255), int(fill_rgb[1] * 255), int(fill_rgb[2] * 255), 255)

        # Контур: комплементарный (противоположный) цвет на цветовом круге (+180 градусов / +0.5 к Hue)
        # Делаем его насыщенным и достаточно ярким
        stroke_h = (h + 0.5) % 1.0
        stroke_rgb = colorsys.hsv_to_rgb(stroke_h, max(s, 0.7), 0.9)
        stroke_color = (int(stroke_rgb[0] * 255), int(stroke_rgb[1] * 255), int(stroke_rgb[2] * 255), 255)

        # Тень на темном фоне: глубокий черный с мягкой прозрачностью (альфа = 160 из 255)
        shadow_color = (0, 0, 0, 160)

    else:
        # --- НА СВЕТЛОМ ФОНЕ ---
        # Тело букв: очень темный оттенок, близкий к черному или глубокому монохрому фона
        fill_rgb = colorsys.hsv_to_rgb(h, s * 0.2, 0.15)
        fill_color = (int(fill_rgb[0] * 255), int(fill_rgb[1] * 255), int(fill_rgb[2] * 255), 255)

        # Контур: комплементарный цвет, но уплавненный по яркости вниз, чтобы не резал глаза
        stroke_h = (h + 0.5) % 1.0
        stroke_rgb = colorsys.hsv_to_rgb(stroke_h, max(s, 0.8), 0.4)
        stroke_color = (int(stroke_rgb[0] * 255), int(stroke_rgb[1] * 255), int(stroke_rgb[2] * 255), 255)

        # Тень на светлом фоне: сильно затененная версия самого фона (собственная тень) + прозрачность
        shadow_rgb = colorsys.hsv_to_rgb(h, min(s * 1.5, 1.0), max(v * 0.3, 0.05))
        shadow_color = (int(shadow_rgb[0] * 255), int(shadow_rgb[1] * 255), int(shadow_rgb[2] * 255), 130)

    # Если фон изначально серый/белый/черный (нет насыщенности), комплементарный цвет вернет тот же серый.
    # Сделаем явную страховку для монохромных фонов:
    if s < 0.05:
        if is_dark_bg:
            stroke_color = (255, 0, 0, 255)  # На черном фоне контур будет классическим красным
        else:
            stroke_color = (0, 0, 128, 255)  # На белом фоне контур будет глубоким синим

    return GeneratedPalette(
        fill_color=fill_color, stroke_color=stroke_color, shadow_color=shadow_color
    )
