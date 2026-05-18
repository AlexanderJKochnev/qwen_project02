# app.core.utils.image_processor.py
"""
обработка изображегниий с детерминированным результатом (для того что бы по хешам дедуплицировать входные данные
"""
import asyncio
import io
import gc
import logging
import os
import random
from typing import Tuple, Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from PIL import Image, ImageOps
import numpy as np
import onnxruntime as ort


# Импортируем rembg на уровне модуля
from rembg import remove, new_session

logger = logging.getLogger(__name__)


@dataclass
class ImageProcessingConfig:
    """Конфигурация обработки изображений"""

    # Размеры
    max_full_width: int = 1200
    max_full_height: int = 1200
    max_thumb_width: int = 150
    max_thumb_height: int = 150
    max_file_size_bytes: int = 100 * 1024  # 100 KB

    # WebP настройки
    webp_lossless: bool = True
    webp_quality: int = 85  # Для lossy режима (1-100)
    webp_method: int = 6  # 0-6, 6 = максимальное сжатие
    webp_alpha_quality: int = 90  # Качество альфа-канала (0-100)
    webp_exact: bool = True  # Бит-ту-бит сохранение

    # Настройки прозрачности
    alpha_threshold: int = 128  # Бинаризация альфа-канала (0-255)
    margin_pct: float = 0.05  # Отступ при кропе

    # U²-Net настройки
    rembg_model: str = "u2net"  # u2net, u2net_human_seg, u2net_cloth_seg, isnet-anime
    rembg_seed: int = 42  # Seed для детерминированности (используется только при deterministic_mode=True)

    # Режимы работы
    deterministic_mode: bool = True  # True: детерминированно (медленнее), False: производительно (быстрее)
    rembg_num_threads_deterministic: int = 1  # Потоков в детерминированном режиме
    rembg_num_threads_fast: int = 4  # Потоков в быстром режиме

    # Производительность
    max_workers: int = 4  # Количество потоков для CPU-bound операций
    cleanup_every: int = 5  # Очищать память каждые N изображений

    # Формат сохранения
    save_format: str = "WEBP"  # WEBP, PNG (для отладки)

    def __post_init__(self):
        """Валидация параметров"""
        if self.webp_quality < 1 or self.webp_quality > 100:
            raise ValueError("webp_quality должен быть в диапазоне 1-100")
        if self.webp_alpha_quality < 0 or self.webp_alpha_quality > 100:
            raise ValueError("webp_alpha_quality должен быть в диапазоне 0-100")
        if self.alpha_threshold < 0 or self.alpha_threshold > 255:
            raise ValueError("alpha_threshold должен быть в диапазоне 0-255")
        if self.rembg_num_threads_deterministic < 1:
            raise ValueError("rembg_num_threads_deterministic должен быть >= 1")
        if self.rembg_num_threads_fast < 1:
            raise ValueError("rembg_num_threads_fast должен быть >= 1")

    @property
    def rembg_num_threads(self) -> int:
        """Возвращает количество потоков в зависимости от режима"""
        if self.deterministic_mode:
            return self.rembg_num_threads_deterministic
        else:
            return self.rembg_num_threads_fast


class ImageProcessor:
    """
    Детерминированная/производительная обработка изображений с поддержкой:
    - Удаления фона (U²-Net) с настраиваемым детерминизмом
    - Ресайза с сохранением пропорций
    - Конвертации в WebP (lossless/lossy)
    - Пакетной обработки с очисткой памяти
    """

    def __init__(self, config: ImageProcessingConfig = None):
        self.config = config or ImageProcessingConfig()
        self._rembg_session = None
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._batch_counter = 0

        # Устанавливаем детерминированные настройки (если включено)
        if self.config.deterministic_mode:
            self._setup_deterministic_environment()
        else:
            self._setup_performance_environment()

        # Загружаем сессию rembg с соответствующими настройками
        self._init_rembg_session()

        mode_str = "детерминированный" if self.config.deterministic_mode else "производительный"
        logger.info(
            f"ImageProcessor инициализирован: режим={mode_str}, "
            f"lossless={self.config.webp_lossless}, "
            f"threads={self.config.rembg_num_threads}, "
            f"model={self.config.rembg_model}"
        )

    def _setup_deterministic_environment(self):
        """
        Установка детерминированного окружения для ONNX Runtime
        Эти переменные должны быть установлены ДО импорта тяжелых библиотек
        """
        # Системные переменные
        os.environ["OMP_NUM_THREADS"] = str(self.config.rembg_num_threads_deterministic)
        os.environ["PYTHONHASHSEED"] = str(self.config.rembg_seed)

        # Устанавливаем seed для Python и NumPy
        if self.config.rembg_seed is not None:
            random.seed(self.config.rembg_seed)
            np.random.seed(self.config.rembg_seed)
            logger.debug(f"Детерминированный режим: seed={self.config.rembg_seed}")

    def _setup_performance_environment(self):
        """
        Установка производительного окружения (без ограничений)
        """
        # Убираем ограничения на потоки
        if "OMP_NUM_THREADS" in os.environ:
            del os.environ["OMP_NUM_THREADS"]
        if "PYTHONHASHSEED" in os.environ:
            del os.environ["PYTHONHASHSEED"]

        logger.debug(f"Производительный режим: без ограничений, threads={self.config.rembg_num_threads_fast}")

    def _init_rembg_session(self):
        """
        Инициализация сессии ONNX Runtime для rembg
        """
        # Настройка ONNX Runtime
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = self.config.rembg_num_threads
        opts.inter_op_num_threads = self.config.rembg_num_threads

        if self.config.deterministic_mode:
            # Детерминированный режим
            opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            opts.enable_cpu_mem_arena = False
            opts.enable_mem_pattern = False
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
            logger.debug(f"ONNX Runtime: детерминированный режим, threads={self.config.rembg_num_threads}")
        else:
            # Производительный режим
            opts.execution_mode = ort.ExecutionMode.ORT_PARALLEL
            opts.enable_cpu_mem_arena = True
            opts.enable_mem_pattern = True
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            logger.debug(f"ONNX Runtime: производительный режим, threads={self.config.rembg_num_threads}")

        try:
            self._rembg_session = new_session(
                model_name=self.config.rembg_model, providers=["CPUExecutionProvider"], sess_opts=opts
            )
            logger.info(f"Модель rembg загружена: {self.config.rembg_model}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {self.config.rembg_model}: {e}")
            # Пробуем загрузить стандартную модель
            try:
                logger.warning("Пробуем загрузить стандартную модель u2net")
                self._rembg_session = new_session(
                    model_name="u2net", providers=["CPUExecutionProvider"], sess_opts=opts
                )
                logger.info("Стандартная модель u2net загружена")
            except Exception as e2:
                logger.error(f"Не удалось загрузить ни одну модель: {e2}")
                self._rembg_session = None

    # ==================== ПУБЛИЧНЫЕ МЕТОДЫ ====================

    async def process_single(
            self, image_bytes: bytes, remove_bg: bool = True
    ) -> Tuple[bytes, bytes, Dict[str, Any]]:
        """
        Обработка одного изображения (асинхронно)

        Args:
            image_bytes: исходное изображение в bytes
            remove_bg: удалять ли фон

        Returns:
            (full_webp_bytes, thumb_webp_bytes, metadata)
        """
        return await self._process_single_async(image_bytes, remove_bg)

    async def process_batch(
            self, images: List[bytes], remove_bg: bool = True, cleanup_every: int = None
    ) -> List[Tuple[bytes, bytes, Dict[str, Any]]]:
        """
        Пакетная обработка изображений с очисткой памяти

        Args:
            images: список исходных изображений
            remove_bg: удалять ли фон
            cleanup_every: очищать память каждые N изображений (берется из config если None)

        Returns:
            список результатов (full_webp, thumb_webp, metadata)
        """
        cleanup_every = cleanup_every or self.config.cleanup_every
        results = []
        total = len(images)

        logger.info(f"Начало пакетной обработки {total} изображений, cleanup_every={cleanup_every}")

        for idx, img_bytes in enumerate(images):
            try:
                # Обработка одного изображения
                result = await self._process_single_async(img_bytes, remove_bg)
                results.append(result)

                # Периодическая очистка памяти
                if (idx + 1) % cleanup_every == 0:
                    await self._cleanup_memory()
                    logger.debug(f"Обработано {idx + 1}/{total}, выполнена очистка памяти")

                # Принудительный сбор мусора для больших пакетов
                if (idx + 1) % (cleanup_every * 10) == 0:
                    gc.collect()
                    logger.debug(f"Выполнен принудительный GC после {idx + 1} изображений")

            except Exception as e:
                logger.error(f"Ошибка обработки изображения {idx}: {e}", exc_info=True)
                results.append((None, None, {"error": str(e), "index": idx}))

        # Финальная очистка
        await self._cleanup_memory()
        gc.collect()

        success_count = len([r for r in results if r[0] is not None])
        logger.info(f"Пакетная обработка завершена. Успешно: {success_count}/{total}")
        return results

    def process_single_sync(
            self, image_bytes: bytes, remove_bg: bool = True
    ) -> Tuple[bytes, bytes, Dict[str, Any]]:
        """
        Синхронная версия для простых случаев
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.process_single(image_bytes, remove_bg)
            )
        finally:
            loop.close()

    # ==================== ВНУТРЕННИЕ МЕТОДЫ ====================

    async def _process_single_async(
            self, image_bytes: bytes, remove_bg: bool
    ) -> Tuple[bytes, bytes, Dict[str, Any]]:
        """
        Основная асинхронная обработка
        """
        # 1. Загрузка и подготовка
        image, metadata = await self._load_and_prepare(image_bytes)

        # 2. Удаление фона (опционально)
        if remove_bg and self._rembg_session:
            image = await self._remove_background_async(image)
            image = self._normalize_alpha_channel(image)
            image = self._smart_crop(image)

        # 3. Создание full-изображения
        full_data = await self._create_full_image(image)

        # 4. Создание thumbnail
        thumb_data = await self._create_thumbnail(image)

        # 5. Метаданные
        metadata.update(
            {'full_size_bytes': len(full_data), 'thumb_size_bytes': len(thumb_data),
             'full_mime': f'image/{self.config.save_format.lower()}',
             'thumb_mime': f'image/{self.config.save_format.lower()}', 'has_alpha': image.mode == 'RGBA',
             'mode': 'deterministic' if self.config.deterministic_mode else 'performance',
             'config': {'deterministic_mode': self.config.deterministic_mode,
                        'lossless': self.config.webp_lossless,
                        'quality': self.config.webp_quality if not self.config.webp_lossless else None,
                        'rembg_seed': self.config.rembg_seed if self.config.deterministic_mode else None,
                        'rembg_model': self.config.rembg_model,
                        'rembg_num_threads': self.config.rembg_num_threads}}
        )

        return full_data, thumb_data, metadata

    async def _load_and_prepare(self, image_bytes: bytes) -> Tuple[Image.Image, Dict]:
        """Загрузка и подготовка изображения"""
        loop = asyncio.get_event_loop()

        def _load():
            img = Image.open(io.BytesIO(image_bytes))
            img = ImageOps.exif_transpose(img)
            return img

        image = await loop.run_in_executor(self._executor, _load)

        metadata = {'original_format': image.format, 'original_mode': image.mode, 'original_size': image.size}

        return image, metadata

    async def _remove_background_async(self, image: Image.Image) -> Image.Image:
        """Асинхронное удаление фона через настроенную сессию rembg"""
        loop = asyncio.get_event_loop()

        def _remove_bg():
            # Конвертируем в RGB для лучших результатов
            if image.mode == 'RGBA':
                rgb_img = Image.new('RGB', image.size, (255, 255, 255))
                rgb_img.paste(image, mask=image.split()[-1])
            else:
                rgb_img = image.convert('RGB')

            # Используем созданную сессию (уже настроена под выбранный режим)
            result = remove(rgb_img, session=self._rembg_session)
            return result.convert('RGBA')

        return await loop.run_in_executor(self._executor, _remove_bg)

    def _normalize_alpha_channel(self, image: Image.Image) -> Image.Image:
        """Нормализация альфа-канала для детерминированности"""
        if image.mode != 'RGBA':
            return image

        r, g, b, a = image.split()
        binary_alpha = a.point(lambda p: 255 if p > self.config.alpha_threshold else 0)
        return Image.merge('RGBA', (r, g, b, binary_alpha))

    def _smart_crop(self, image: Image.Image) -> Image.Image:
        """Умный кроп с выравниванием до четных размеров"""
        bbox = image.getbbox()
        if not bbox:
            return image

        obj_w = bbox[2] - bbox[0]
        obj_h = bbox[3] - bbox[1]
        margin = int(max(obj_w, obj_h) * self.config.margin_pct)

        left = max(0, bbox[0] - margin)
        top = max(0, bbox[1] - margin)
        right = min(image.width, bbox[2] + margin)
        bottom = min(image.height, bbox[3] + margin)

        # Выравнивание до четных
        if (right - left) % 2:
            right = min(image.width, right + 1)
        if (bottom - top) % 2:
            bottom = min(image.height, bottom + 1)

        cropped = image.crop((left, top, right, bottom))

        # Убираем прозрачную кайму (быстрая проверка по углам)
        if cropped.mode == 'RGBA' and cropped.width > 0 and cropped.height > 0:
            alpha = cropped.split()[-1]
            try:
                if alpha.getpixel((cropped.width // 2, 0)) < 10:
                    cropped = cropped.crop((0, 1, cropped.width, cropped.height))
                if cropped.height > 0 and alpha.getpixel((0, cropped.height // 2)) < 10:
                    cropped = cropped.crop((1, 0, cropped.width, cropped.height))
            except IndexError:
                pass

        return cropped

    async def _create_full_image(self, image: Image.Image) -> bytes:
        """Создание full-изображения с контролем размера"""
        loop = asyncio.get_event_loop()

        def _create():
            temp_img = image.copy()

            # Ресайз до максимальных размеров
            temp_img.thumbnail(
                (self.config.max_full_width, self.config.max_full_height), Image.Resampling.LANCZOS
            )

            # Сохраняем в выбранном формате
            data = self._save_image(temp_img)

            # Проверка размера (если превышает - уменьшаем)
            if len(data) > self.config.max_file_size_bytes:
                scale = 0.9
                while len(data) > self.config.max_file_size_bytes and scale > 0.4:
                    new_size = tuple(int(dim * scale) for dim in temp_img.size)
                    temp_img = temp_img.resize(new_size, Image.Resampling.LANCZOS)
                    data = self._save_image(temp_img)
                    scale -= 0.1

            return data

        return await loop.run_in_executor(self._executor, _create)

    def _save_image(self, image: Image.Image) -> bytes:
        """
        Сохранение изображения с учетом настроек формата
        """
        buf = io.BytesIO()

        if self.config.save_format.upper() == "WEBP":
            save_kwargs = {'format': 'WEBP', 'method': self.config.webp_method,
                           'exact': self.config.webp_exact if self.config.webp_lossless else False, }

            if self.config.webp_lossless:
                save_kwargs['lossless'] = True
                save_kwargs['quality'] = 100
                save_kwargs['alpha_quality'] = self.config.webp_alpha_quality
            else:
                save_kwargs['lossless'] = False
                save_kwargs['quality'] = self.config.webp_quality
                save_kwargs['alpha_quality'] = self.config.webp_alpha_quality

            image.save(buf, **save_kwargs)

        elif self.config.save_format.upper() == "PNG":
            # Для отладки или особых случаев
            image.save(buf, format='PNG', optimize=True, compress_level=9)

        else:
            raise ValueError(f"Unsupported format: {self.config.save_format}")

        return buf.getvalue()

    async def _create_thumbnail(self, image: Image.Image) -> bytes:
        """Создание thumbnail"""
        loop = asyncio.get_event_loop()

        def _create():
            thumb = image.copy()

            # Приводим к RGBA
            if thumb.mode != 'RGBA':
                thumb = thumb.convert('RGBA')

            # Ресайз с сохранением пропорций
            thumb.thumbnail(
                (self.config.max_thumb_width, self.config.max_thumb_height), Image.Resampling.LANCZOS
            )

            # Квадратный канвас
            square = Image.new(
                'RGBA', (self.config.max_thumb_width, self.config.max_thumb_height), (0, 0, 0, 0)
            )
            x = (self.config.max_thumb_width - thumb.width) // 2
            y = (self.config.max_thumb_height - thumb.height) // 2
            square.paste(thumb, (x, y))

            # Для thumbnail всегда используем WebP lossless (максимум качества)
            buf = io.BytesIO()
            square.save(
                buf, format='WEBP', lossless=True, method=min(4, self.config.webp_method), exact=True,
                alpha_quality=self.config.webp_alpha_quality
            )

            return buf.getvalue()

        return await loop.run_in_executor(self._executor, _create)

    async def _cleanup_memory(self):
        """Очистка памяти для предотвращения артефактов"""
        loop = asyncio.get_event_loop()

        def _clean():
            # Очищаем кэш PIL
            Image._initialized = False

        await loop.run_in_executor(self._executor, _clean)
        self._batch_counter += 1

    # ==================== МЕТОДЫ ДЛЯ ТЕСТИРОВАНИЯ ====================

    async def shutdown(self):
        """Корректное завершение работы"""
        if self._rembg_session is not None:
            del self._rembg_session
            self._rembg_session = None
        self._executor.shutdown(wait=True)
        logger.info("ImageProcessor завершил работу")

    def get_config_info(self) -> Dict[str, Any]:
        """Получить информацию о текущей конфигурации"""
        return {'deterministic_mode': self.config.deterministic_mode, 'lossless': self.config.webp_lossless,
                'quality': self.config.webp_quality if not self.config.webp_lossless else 'N/A',
                'rembg_model': self.config.rembg_model,
                'rembg_seed': self.config.rembg_seed if self.config.deterministic_mode else None,
                'rembg_num_threads': self.config.rembg_num_threads, 'max_workers': self.config.max_workers,
                'save_format': self.config.save_format, 'max_file_size_bytes': self.config.max_file_size_bytes}

    def is_rembg_available(self) -> bool:
        """Проверка доступности модели rembg"""
        return self._rembg_session is not None

    def switch_mode(self, deterministic: bool):
        """
        Переключение режима работы (требует перезагрузки модели)

        Args:
            deterministic: True - детерминированный, False - производительный
        """
        if self.config.deterministic_mode == deterministic:
            logger.info(f"Режим уже установлен: {'детерминированный' if deterministic else 'производительный'}")
            return

        self.config.deterministic_mode = deterministic
        # Перезагружаем сессию с новыми настройками
        self._init_rembg_session()

        mode_str = "детерминированный" if deterministic else "производительный"
        logger.info(f"Переключен режим: {mode_str}, threads={self.config.rembg_num_threads}")


# ==================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ====================

async def example_usage():
    # Пример 1: Детерминированный режим (для дедупликации)
    config_deterministic = ImageProcessingConfig(
        max_full_width=1024, max_full_height=1024, max_thumb_width=200, max_thumb_height=200,
        webp_lossless=True, deterministic_mode=True,  # Включаем детерминизм
        rembg_seed=42, rembg_num_threads_deterministic=1, rembg_model="u2net"
    )

    # Пример 2: Производительный режим (для быстрой обработки)
    config_fast = ImageProcessingConfig(
        max_full_width=1024, max_full_height=1024, max_thumb_width=200, max_thumb_height=200,
        webp_lossless=False,  # Lossy для скорости и размера
        webp_quality=80, deterministic_mode=False,  # Отключаем детерминизм
        rembg_num_threads_fast=4, rembg_model="u2net"
    )

    processor_det = ImageProcessor(config_deterministic)
    processor_fast = ImageProcessor(config_fast)

    print(f"Детерминированный режим: {processor_det.get_config_info()}")
    print(f"Производительный режим: {processor_fast.get_config_info()}")

    # Обработка с демонстрацией разницы в скорости
    with open('input.png', 'rb') as f:
        image_bytes = f.read()

    import time

    # Тест детерминированного режима
    start = time.time()
    full_det, thumb_det, meta_det = await processor_det.process_single(image_bytes, remove_bg=True)
    det_time = time.time() - start

    # Тест производительного режима
    start = time.time()
    full_fast, thumb_fast, meta_fast = await processor_fast.process_single(image_bytes, remove_bg=True)
    fast_time = time.time() - start

    print(f"\nРезультаты:")
    print(f"  Детерминированный: {det_time:.2f}s, размер={len(full_det)} bytes")
    print(f"  Производительный: {fast_time:.2f}s, размер={len(full_fast)} bytes")
    print(f"  Ускорение: {det_time / fast_time:.1f}x")

    # Сохраняем результаты
    with open('output_deterministic.webp', 'wb') as f:
        f.write(full_det)
    with open('output_fast.webp', 'wb') as f:
        f.write(full_fast)

    # Пакетная обработка в производительном режиме
    images = [image_bytes] * 10
    results = await processor_fast.process_batch(images, remove_bg=True, cleanup_every=3)

    print(f"\nПакетная обработка: {len([r for r in results if r[0] is not None])}/{len(images)} успешно")

    # Динамическое переключение режима
    print("\nПереключаем режим на лету...")
    processor_fast.switch_mode(deterministic=True)
    print(f"Новый режим: deterministic={processor_fast.config.deterministic_mode}")

    await processor_det.shutdown()
    await processor_fast.shutdown()


if __name__ == '__main__':
    asyncio.run(example_usage())
