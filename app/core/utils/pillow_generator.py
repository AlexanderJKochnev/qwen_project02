import io
# import os
import string
from dataclasses import dataclass
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from app.core.config.project_config import settings
from app.core.utils.io_utils import get_dirpath
from app.core.utils.color_palette import auto_match_colors, GeneratedPalette


"""
    генератор изображений из текста
    может подбирать цвета под цвет подложки
"""


def hex_to_rgba_byte(hex_str, alpha=255):
    num = int(hex_str.lstrip('#'), 16)
    return (num >> 16) & 255, (num >> 8) & 255, num & 255, int(alpha)


@dataclass
class TextConfig:
    """Конфигурация параметров генерации текстового изображения."""
    text: str
    font_path: str = 'glouchester.ttf'
    background_color: str | Tuple[int, int, int, int] = (255, 255, 255, 0)
    background_opacity: int = 255
    fill_color: str | Tuple[int, int, int, int] = (0, 0, 0, 0)
    stroke_color: str | Tuple[int, int, int, int] = "black"
    shadow_color: Optional[str | Tuple[int, int, int, int]] = "rgba(0, 0, 0, 128)"

    width: int = settings.TXT_WEIGHT
    height: int = settings.TXT_HEIGHT
    initial_font_size: int = settings.TXT_FONT_SIZE
    shadow_offset: Optional[Tuple[int, int]] = (settings.TXT_SHADOW_X, settings.TXT_SHADOW_Y)
    padding: int = settings.TXT_PADDING
    fill_opacity: int = settings.TXT_FILL_OPACITY  # По умолчанию прозрачные буквы внутри
    shadow_opacity: int = settings.TXT_SHADOW_OPACITY  # По умолчанию полупрозрачная тень
    # Минимальная длина слова, которое может стоять ОДНО на строке.
    # Если слово меньше или РАВНО этой длине, оно не может быть одно.
    min_word_length: int = settings.TXT_MIN_WORD_LENGTH
    stroke_width: int = settings.TXT_STROKE_WIDTH
    text_alignment: str = settings.TXT_ALIGNMENT

    def __post_init__(self):
        """Автоматически подмешивает прозрачность к цветам после создания объекта."""
        self.fill_color = tuple([*self.fill_color[:3], self.fill_opacity])
        if self.shadow_color:
            self.shadow_color = tuple([*self.shadow_color[:3], self.shadow_opacity])
        txt = ' '.join(self.text.replace('«', '').replace('»', '').split())
        self.text = __import__('functools').reduce(lambda t, x: t.replace(f'{x} ', '\n'), ',.;:', txt.rstrip('.'))
        fonts_dir = get_dirpath('fonts')
        self.font_path = f'{fonts_dir}/{self.font_path}'    # путь к шрифту
        if isinstance(self.background_color, str) and self.background_color.startswith('#'):
            self.background_color = hex_to_rgba_byte(self.background_color, self.background_opacity)
        else:
            self.background_color = tuple([*self.background_color[:3], self.background_opacity])


@dataclass
class TextConfigAdaptive:
    """ Конфигурация параметров генерации текстового изображения.
        с адаптивной настройкой палитры
    """
    text: str
    font_path: str = 'glouchester.ttf'
    background_color: str | Tuple[int, int, int, int] = (255, 255, 255, 0)

    background_opacity: int = 0
    width: int = settings.TXT_WEIGHT
    height: int = settings.TXT_HEIGHT
    initial_font_size: int = settings.TXT_FONT_SIZE
    shadow_offset: Optional[Tuple[int, int]] = (settings.TXT_SHADOW_X, settings.TXT_SHADOW_Y)
    padding: int = settings.TXT_PADDING
    fill_opacity: int = settings.TXT_FILL_OPACITY  # По умолчанию прозрачные буквы внутри
    shadow_opacity: int = settings.TXT_SHADOW_OPACITY  # По умолчанию полупрозрачная тень
    # Минимальная длина слова, которое может стоять ОДНО на строке.
    # Если слово меньше или РАВНО этой длине, оно не может быть одно.
    min_word_length: int = settings.TXT_MIN_WORD_LENGTH
    stroke_width: int = settings.TXT_STROKE_WIDTH
    text_alignment: str = settings.TXT_ALIGNMENT

    def __post_init__(self):
        """Автоматически подмешивает прозрачность к цветам после создания объекта."""
        if isinstance(self.background_color, str) and self.background_color.startswith('#'):
            self.background_color = hex_to_rgba_byte(self.background_color, alpha=self.background_opacity)
        pallette: GeneratedPalette = auto_match_colors(self.background_color, self.fill_opacity, self.shadow_opacity)
        self.fill_color = tuple([*pallette.fill_color[:3], self.fill_opacity])
        self.shadow_color = tuple([*pallette.shadow_color[:3], self.shadow_opacity])
        txt = ' '.join(self.text.replace('«', '').replace('»', '').split())
        self.text = __import__('functools').reduce(lambda t, x: t.replace(f'{x} ', '\n'), ',.;:', txt.rstrip('.'))
        fonts_dir = get_dirpath('fonts')
        self.font_path = f'{fonts_dir}/{self.font_path}'    # путь к шрифту
        if isinstance(self.background_color, str) and self.background_color.startswith('#'):
            self.background_color = hex_to_rgba_byte(self.background_color, self.background_opacity)
        else:
            self.background_color = tuple([*self.background_color[:3], self.background_opacity])


def should_allow_single_word(word: str, min_length: int) -> bool:
    """
    Проверяет, разрешено ли слову стоять в строке в одиночестве.
    Возвращает True, если слово разрешено оставлять одно.
    """
    if min_length == 0:
        return True

    # Очищаем слово от знаков препинания (например, "me," -> "me"), чтобы правильно считать длину
    clean_word = word.strip(string.punctuation)

    if not clean_word:  # Если остались только знаки препинания
        return True

    if clean_word.isdigit():
        return True

    if clean_word.isupper() and clean_word.isalpha():  # Чистый КАПС
        return True

    # ИСПРАВЛЕНО: Если длина строго БОЛЬШЕ лимита — разрешаем.
    # Если равна лимиту или меньше — запрещаем (вернет False).
    if len(clean_word) > min_length:
        return True

    return False


def wrap_and_fit_text(config: TextConfig) -> Tuple[List[str], ImageFont.FreeTypeFont, int, int]:
    """
    Разбивает текст по словам с учетом оригинальных \\n.
    Если получившиеся строки нарушают правило min_word_length,
    размер шрифта уменьшается до тех пор, пока условие не выполнится.
    """
    if not config.text.strip():
        raise ValueError("Передан пустой текст для отрисовки")

    max_w = config.width - (config.padding * 2)
    max_h = config.height - (config.padding * 2)

    shadow_max = max(config.shadow_offset) if config.shadow_offset else 0
    extra_w = shadow_max + config.stroke_width * 2
    extra_h = shadow_max + config.stroke_width * 2
    max_w -= extra_w
    max_h -= extra_h

    font_size = config.initial_font_size

    while font_size > 5:
        font = ImageFont.truetype(config.font_path, font_size)
        all_final_lines = []
        is_step_valid = True  # Флаг валидности текущего размера шрифта

        paragraphs = config.text.split('\n')

        for paragraph in paragraphs:
            words = paragraph.split()
            if not words:
                all_final_lines.append("")
                continue

            # ИСКЛЮЧЕНИЕ: Если в исходном абзаце изначально всего 1 слово,
            # у нас нет выбора, кроме как оставить его одного.
            if len(words) == 1:
                bbox = font.getbbox(words[0])
                if (bbox[2] - bbox[0]) > max_w:
                    is_step_valid = False
                    break
                all_final_lines.append(words[0])
                continue

            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word]) if current_line else word
                bbox = font.getbbox(test_line)
                line_w = bbox[2] - bbox[0]

                if line_w <= max_w:
                    current_line.append(word)
                else:
                    if not current_line:
                        # Даже одно слово не влезло в пустую строку
                        is_step_valid = False
                        break

                    # Завершаем текущую строку
                    all_final_lines.append(' '.join(current_line))
                    current_line = [word]

            if not is_step_valid:
                break

            if current_line:
                all_final_lines.append(' '.join(current_line))

        # Если базовое разбиение по ширине прошло без критических ошибок,
        # запускаем ЖЕСТКУЮ проверку нашего правила для ВСЕХ получившихся строк.
        if is_step_valid:
            for line in all_final_lines:
                line_words = line.split()
                # Если в строке оказалось всего одно слово
                if len(line_words) == 1:
                    single_word = line_words[0]

                    # Проверяем: было ли это слово ЕДИНСТВЕННЫМ во всем исходном абзаце?
                    # Нам нужно найти оригинальный абзац, которому принадлежит это слово.
                    # Если в оригинальном абзаце слов было больше, значит это одиночество — результат переноса!
                    is_originally_alone = False
                    for orig_p in paragraphs:
                        orig_words = orig_p.split()
                        if len(orig_words) == 1 and single_word in orig_words:
                            is_originally_alone = True
                            break

                    # Если слово осталось одно из-за переноса, и оно НЕ удовлетворяет правилу длины
                    if not is_originally_alone and not should_allow_single_word(single_word, config.min_word_length):
                        logger.debug(f"Шрифт {font_size}px не подошел: слово '{single_word}' нарушает min_word_length")
                        is_step_valid = False
                        break

        # Шаг 3: Если шаг всё еще валиден, проверяем габариты всего блока текста
        if is_step_valid:
            temp_img = Image.new("RGBA", (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)

            multiline_text = '\n'.join(all_final_lines)
            block_bbox = temp_draw.multiline_textbbox(
                (0, 0), multiline_text, font=font, align=config.text_alignment
            )

            block_w = block_bbox[2] - block_bbox[0]
            block_h = block_bbox[3] - block_bbox[1]

            # Если текст уложился в рамки холста — возвращаем результат
            if block_h <= max_h and block_w <= max_w:
                logger.info(f"Успешно подобрано! Итоговый шрифт: {font_size}px")
                return all_final_lines, font, block_w, block_h

        # Если шаг невалиден (из-за нарушения правила или габаритов), строго уменьшаем шрифт
        font_size -= 2

    raise ValueError("Текст невозможно уместить с соблюдением всех правил даже минимальным шрифтом.")


def generate_text_image(config: TextConfig, format: str = 'WEBP', quality: int = 100) -> bytes:
    """Генерирует изображение на основе переданного объекта TextConfig."""
    try:
        # Шаг 1: Рассчитываем перенос строк и размер шрифта
        lines, font, block_w, block_h = wrap_and_fit_text(config)
        full_text = '\n'.join(lines)

        # Шаг 2: Создаем холст ИЗНАЧАЛЬНО полностью прозрачным
        logger.debug("Шаг 2: Создание прозрачного холста...")
        img_trans = Image.new("RGBA", (config.width, config.height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img_trans)

        # Шаг 3: Расчет координат (Левый верхний угол текстового блока = padding, padding)
        start_x = config.padding
        start_y = config.padding

        # Шаг 4: Отрисовка тени (если включена)
        if config.shadow_offset and config.shadow_color:
            logger.debug("Шаг 4: Отрисовка эффекта тени...")
            shadow_x = start_x + config.shadow_offset[0]
            shadow_y = start_y + config.shadow_offset[1]
            draw.multiline_text(
                (shadow_x, shadow_y), full_text, font=font, fill=config.shadow_color,
                align=config.text_alignment
            )

        # Шаг 5: Отрисовка основного текста с контуром
        logger.debug("Шаг 5: Отрисовка основного текста с обводкой...")
        draw.multiline_text(
            (start_x, start_y), full_text, font=font, fill=config.fill_color,
            stroke_width=config.stroke_width, stroke_fill=config.stroke_color, align=config.text_alignment
        )

        # Шаг 5.5: Обрезаем холст по ширине текстового блока + padding
        # Вычисляем реальную ширину текстового блока (с учётом тени)
        text_bbox = draw.textbbox((start_x, start_y), full_text, font=font)
        shadow_bbox = None
        if config.shadow_offset and config.shadow_color:
            shadow_bbox = draw.textbbox((shadow_x, shadow_y), full_text, font=font)
            # Объединяем bounding box текста и тени
            combined_bbox = (min(text_bbox[0], shadow_bbox[0]), min(text_bbox[1], shadow_bbox[1]),
                             max(text_bbox[2], shadow_bbox[2]), max(text_bbox[3], shadow_bbox[3]))
        else:
            combined_bbox = text_bbox

        # Новая ширина = ширина блока + padding*2
        # new_width = combined_bbox[2] - combined_bbox[0] + config.padding * 2
        # new_height = combined_bbox[3] - combined_bbox[1] + config.padding * 2

        # Обрезаем изображение
        img_trans = img_trans.crop(
            (combined_bbox[0] - config.padding, combined_bbox[1] - config.padding,
             combined_bbox[2] + config.padding, combined_bbox[3] + config.padding)
        )

        # МЕТАДАННЫЕ: Сохраняем исходный текст в структуру WEBP/PNG/JPEG
        from PIL.PngImagePlugin import PngInfo
        metadata = PngInfo()
        metadata.add_text('comment', f'{config.text}, text_generated')
        metadata.add_text('custom:original_text', f'{config.text}, text_generated')

        # Шаг 6: Сохраняем прозрачный файл
        buffer = io.BytesIO()
        save_kwargs = {'format': format}
        if format in ('JPEG', 'WEBP'):
            save_kwargs['quality'] = quality
        if config.background_opacity == 0:
            img_trans.save(buffer, **save_kwargs)
            trans_bytes = buffer.getvalue()
            return trans_bytes
        # 1. Создаем цветную подложку нужного цвета
        img_solid = Image.new("RGBA", img_trans.size, config.background_color)
        print(config.background_color)
        # 2. Накладываем наш готовый прозрачный текст поверх этой подложки одной командой
        img_solid.alpha_composite(img_trans)
        # 3. Сохраняем цветной файл
        img_solid.save(buffer, **save_kwargs)
        solid_bytes = buffer.getvalue()
        return solid_bytes
    except Exception as e:
        logger.critical(f"ПРОИЗОШЕЛ СБОЙ ПРИ ГЕНЕРАЦИИ! {e}", exc_info=True)


if __name__ == "__main__":
    bg_surface = "#D69456"
    palette = auto_match_colors(bg_surface)
    print(type(palette.fill_color))
    fill_color, stroke_color, shadow_color = palette.fill_color, palette.stroke_color, palette.shadow_color
    print(fill_color)
    # opacity = 125
    # fill_color = tuple([*fill_color[:-1], opacity])
    # print(fill_color)
    config = TextConfig(
        text="Berta\nTre Soli Tre\nGrappa del Piemonte", width=350, height=500, min_word_length=3,
        text_alignment='center', fill_opacity=50, shadow_opacity=50,

        # Передаем цвета из палитры
        background_color=bg_surface, fill_color=fill_color, stroke_color=palette.stroke_color,
        shadow_color=palette.shadow_color,

        stroke_width=1, shadow_offset=(3, 3)
    )

    target_path = f'/Users/kochnev/PycharmProjects/wine/wand/media/{'_'.join(config.text.lower().split())}.png'

    generate_text_image(config, output_path=target_path)
