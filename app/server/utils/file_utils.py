import io
import os
from uuid import uuid4

import aiofiles
from fastapi import UploadFile, status

from app.server.handler.error_handler import CustomHTTPException
from app.server.logger.custom_logger import logger
from app.server.static import error_identifier

current_path = os.path.dirname(__file__)


def get_app_root_path():
    return os.path.join(current_path, '..', '..')


def get_firebase_credentials_path():
    return os.path.join(get_app_root_path(), 'firebase-adminsdk.json')


def get_file_extension(filename: str, mimetype: str) -> str:
    if not filename and not mimetype:
        return ''
    splitting = filename.rsplit('.', 1)
    if len(splitting) > 1:
        extension = f'.{splitting[1]}'
    else:
        extension = '.' + mimetype.rsplit('/')[1].lower()
        if extension == 'octet-stream':
            extension = ''

    return extension


def get_temp_file_path(folder: str, filename: str = '', mimetype: str = '') -> str:
    """Generates temporary file path to write a file

    Returns:
        str: full file path
    """
    extension = get_file_extension(filename, mimetype)

    folder = folder.replace('/', '/')
    if not folder.endswith('/'):
        folder += '/'
    new_file_name = str(uuid4()) + extension
    return folder + new_file_name


def get_temp_file_name_mimetype(folder: str, mimetype: str) -> str:
    """Generates temporary file path to write a file

    Returns:
        str: full file path
    """
    extension = get_file_extension('', mimetype)

    folder = folder.replace('/', '/')
    if not folder.endswith('/'):
        folder += '/'
    new_file_name = str(uuid4()) + extension
    return folder + new_file_name


async def delete_file(file_path: str) -> None:
    """Deletes the file if it exists in the given file_path

    Args:
        file_path (str): full file path
    """
    if not os.path.exists(file_path):
        logger.debug(f"file path: {file_path} doesn't exist")
    os.remove(file_path)


async def save_file(out_file_path: str, file_bytes: bytes) -> None:
    """Saves file asynchronously to the given path

    Args:
        out_file_path (str): [description]
        in_file (UploadFile): [description]
    """
    async with aiofiles.open(out_file_path, 'wb') as out_file:
        await out_file.write(file_bytes)


def bytes_to_buffer(file_bytes: bytes) -> io.BytesIO:
    """Converts bytes to buffer type object

    Args:
        file (bytes): file content as bytes

    Returns:
        BytesIO: file buffer
    """
    return io.BytesIO(file_bytes)


async def read_file(filepath):
    """Read file as bytes

    Args:
        filepath (str): file path

    Returns:
        bytes: file bytes
    """
    async with aiofiles.open(filepath, mode='rb') as file:
        contents = await file.read()
    return contents


def get_file_name(filepath: str) -> str:
    """Gets file name from file path

    Args:
        filepath (str): file path

    Returns:
        str: file name
    """
    splitting = filepath.rsplit('/', 1)
    return splitting[1] if len(splitting) > 1 else splitting[0]


def get_preview_image_path(filepath: str) -> str:
    """Gets preview images path

    Args:
        filepath (str): file path

    Returns:
        str: preview image file path
    """
    splitting = filepath.rsplit('/', 1)
    folder = f'{splitting[0]}/'
    filename = splitting[1] if len(splitting) > 1 else splitting[0]
    filename = filename.rsplit('.', 1)[0]
    filename = f'{filename}%s.jpg'
    return folder + filename


def check_allowed_size(file: UploadFile, allowed_size: int) -> bool:
    """
    If the file size is greater than the allowed size, raise an exception

    Args:
      file (UploadFile): UploadFile - this is the file that is being uploaded
      allowed_size (int): The maximum allowed size of the file in KB

    Returns:
      A boolean value.
    """
    if len(file.file.read()) > (allowed_size * 1000):
        raise CustomHTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f'File: {file.filename} size exceeds the allowed size of {allowed_size} KB', identifier=error_identifier.FILE_TOO_LARGE
        )
    file.file.seek(0)
    return True
