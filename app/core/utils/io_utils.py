# app/core/utils/io_utils.py
from pathlib import Path
import json
from typing import List
from app.core.utils.common_utils import enum_to_camel
from app.core.config.project_config import get_path_to_root, settings
# from app.core.utils.alchemy_utils import JsonConverter


def read_file_lines_stripped(filename: Path):
    """ читает файл построчно и возвращает список
        filename имя файла
        dirname директория в которой находится файл (если файл глде-то в боковой ветке)
        для получения filename используй from app.core.utils.common_utils import get_path_to_root
    """
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.rstrip('\n').rstrip(';').strip() for line in file]


def read_enum_to_camel(filename: str = 'country.json') -> dict:
    """
        берет файл в директории загрузки считывает и возвращает словарь
        :param filename:  имя файла
        :type filename:   str
        :return:          {'исходная_строка': 'Исходная Строка'}
        :rtype:           dict
    """
    try:
        upload_dir = settings.UPLOAD_DIR
        file = 'country.json'
        dirname = get_path_to_root(f'{upload_dir}')
        filepath = dirname / file
        result = read_file_lines_stripped(filepath)
        result = {a: enum_to_camel(a) for a in result}
    except Exception as e:
        print(f'read_enum_to_camel.error: {e}')
        result = None
    finally:
        return result


def readJson(filename: Path):
    if filename.exists():
        with open(filename) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data


def get_filepath_from_dir(dirname: str = None,
                          ext_allowed: set = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}) -> List[Path]:
    """
        выводит список файлов (Path) имеющих расширения из ext_allowed
        если ничего не передавно в качестве первого аргумента то ищет здесь upload_dir = settings.UPLOAD_DIR
    """
    if not dirname:
        dir_name = settings.UPLOAD_DIR
    image_dir = get_path_to_root(dir_name)
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_paths = []  # cписок файлов изображений с путями
    for n, file_path in enumerate(image_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_paths.append(file_path)
    return image_paths


def get_filepath_from_dir_by_name(filename: str = None, upload_dir: str = None) -> Path:
    """
    возвращает путь к файлу в определенной директории
    если нет апгументов берет их из .env (data.json from upload_dir
    :param filename:
    :type filename:
    :param upload_dir:
    :type upload_dir:
    :return:
    :rtype:
    """
    try:
        if not filename:
            filename = settings.JSON_FILENAME  # имя файла для импорта
        if not upload_dir:
            upload_dir = settings.UPLOAD_DIR
        dirpath: Path = get_path_to_root(upload_dir)
        filepath = dirpath / filename
        return filepath
    except Exception:
        raise Exception(f'file {filename} is not exists in {upload_dir}')
