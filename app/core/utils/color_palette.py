import colorsys
from typing import Tuple
from PIL import ImageColor
from dataclasses import dataclass
from loguru import logger


@dataclass
class GeneratedPaletteSHIT:
    """Результат автоматического подбора цветов. ГОВНО КОД ДЛЯ СОВМЕСТИМОСТИ"""
    fill_color: Tuple[int, int, int, int]
    stroke_color: Tuple[int, int, int, int]
    shadow_color: Tuple[int, int, int, int]


def auto_match_colors(
        background_color: Tuple[int, int, int, int], fill_opacity: int = 0, shadow_opacity: int = 128
) -> dict:
    """
    Профессиональный подбор гармоничной палитры (Аналоговый сплит + Триада).
    Гарантирует читаемость, задействует прозрачность и избегает банального черного/белого текста.
    """
    try:
        r, g, b = background_color[:3]
        # Переводим в HSV для благородного управления тоном
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    
        # Вычисляем физическую яркость фона (YIQ)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        is_dark_bg = brightness < 125
    
        # Обработка чистых монохромных фонов (серый, белый, черный), где нет цветового тона (s == 0)
        if s < 0.05:
            if is_dark_bg:  # Почти черный фон
                return {"fill_color": (255, 255, 255, fill_opacity),  # Белая основа (высветляет при прозрачности)
                        "stroke_color": (220, 160, 40, 255),  # Благородное золото / охра
                        "shadow_color": (0, 0, 0, shadow_opacity)}
            else:  # Почти белый/светло-серый фон
                return {"fill_color": (20, 20, 20, fill_opacity),  # Темная основа (затемняет при прозрачности)
                        "stroke_color": (40, 70, 120, 255),  # Глубокий сапфировый/чернильный синий
                        "shadow_color": (150, 150, 150, shadow_opacity)}
    
        if is_dark_bg:
            # --- ЛОГИКА ДЛЯ ТЕМНОГО ФОНА ---
            # 1. Тело букв: Высветляющая база. Берем чистый белый (255,255,255)
            # При fill_opacity > 0 этот цвет будет мягко тонировать и высветлять темный фон изнутри.
            fill_color = (255, 255, 255, fill_opacity)
    
            # 2. Окантовка (Stroke): Мягкий аналоговый контраст.
            # Смещаем тон на 30 градусов (0.08 по кругу), делаем его пастельно-ярким (высокая яркость, средняя насыщенность)
            stroke_h = (h + 0.08) % 1.0
            stroke_s = min(s * 0.5 + 0.4, 0.8)  # Не даем уйти в кислоту
            stroke_v = max(v * 2.0, 0.95)  # Делаем контур сочно светящимся
            s_r, s_g, s_b = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(stroke_h, stroke_s, stroke_v))
            stroke_color = (s_r, s_g, s_b, 255)
    
            # 3. Тень: Глубокий, почти черный оттенок цвета самого фона (богатый контражур)
            shadow_v = max(v * 0.2, 0.05)
            sh_r, sh_g, sh_b = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s, shadow_v))
            shadow_color = (sh_r, sh_g, sh_b, shadow_opacity)
    
        else:
            # --- ЛОГИКА ДЛЯ СВЕТЛОГО ФОНА ---
            # 1. Тело букв: Затемняющая база. Берем глубокий монохромный тон самого фона (яркость опускаем до 15%)
            # При fill_opacity > 0 этот цвет будет работать как темный светофильтр, глубоко насыщая и затемняя подложку.
            f_r, f_g, f_b = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, s, 0.15))
            fill_color = (f_r, f_g, f_b, fill_opacity)
    
            # 2. Окантовка (Stroke): Глубокий контрастный тон.
            # Смещаем тон на 45 градусов (0.12 по кругу), делаем цвет очень плотным и насыщенным
            stroke_h = (h + 0.12) % 1.0
            stroke_s = min(s * 1.5, 0.95)
            stroke_v = max(v * 0.3, 0.25)  # Плотный, темный, дорогой оттенок
            s_r, s_g, s_b = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(stroke_h, stroke_s, stroke_v))
            stroke_color = (s_r, s_g, s_b, 255)

            # 3. Тень: Собственная глубокая тень фона (насыщенность выкручиваем, яркость убавляем)
            shadow_s = min(s * 1.8, 1.0)
            shadow_v = max(v * 0.4, 0.3)
            sh_r, sh_g, sh_b = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, shadow_s, shadow_v))
            shadow_color = (sh_r, sh_g, sh_b, shadow_opacity)
            result = {"fill_color": fill_color, "stroke_color": stroke_color, "shadow_color": shadow_color}
            return result
    except Exception as e:
        logger.error(f'auto_match_colors: {e}')
        return None

def auto_match_colors_old(background_color_str: str) -> dict:
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

    return {"fill_color": fill_color,
            "stroke_color": stroke_color,
            "shadow_color": shadow_color}
