import sys
import os

def get_resource_path(relative_path):
    """
    Возвращает путь к ресурсам (например, help.md).
    Работает как в разработке, так и внутри PyInstaller exe.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller создает временную папку _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_app_path():
    """
    Возвращает путь к папке, где лежит исполняемый файл (или скрипт).
    Используется для хранения Базы Данных, чтобы она не удалялась.
    """
    if getattr(sys, 'frozen', False):
        # Если запущено как exe
        return os.path.dirname(sys.executable)
    # Если запущено как скрипт
    return os.path.dirname(os.path.abspath(__file__))