import sys
import os

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_app_path():
    if getattr(sys, 'frozen', False):
        # Если запущено как exe
        return os.path.dirname(sys.executable)
    # Если запущено как скрипт
    return os.path.dirname(os.path.abspath(__file__))