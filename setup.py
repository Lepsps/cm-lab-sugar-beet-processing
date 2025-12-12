import sys
import os
from setuptools import setup, Extension
import pybind11

# Новые пути
src_dir = os.path.join('core', 'src')
inc_dir = os.path.join('core', 'include')

# Флаги компиляции
extra_compile_args = []
if sys.platform == 'win32':
    extra_compile_args = ['/O2']
else:
    extra_compile_args = ['-O3']

# Список исходников (обрати внимание на новые названия файлов)
sources = [
    os.path.join(src_dir, 'sugar_core.cpp'),
    os.path.join(src_dir, 'matrixGenerator.cpp'),
    os.path.join(src_dir, 'hungarian.cpp'),      # Бывший Exact
    os.path.join(src_dir, 'greedy.cpp'),
    os.path.join(src_dir, 'thrifty.cpp'),
    os.path.join(src_dir, 'median.cpp'),
    os.path.join(src_dir, 'greedyThrifty.cpp'),
    os.path.join(src_dir, 'thriftyGreedy.cpp'),
]

ext_modules = [
    Extension(
        'sugar_core',
        sources,
        include_dirs=[
            pybind11.get_include(),
            inc_dir,  # Добавляем путь к заголовкам
            src_dir   # На всякий случай
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
    ),
]

setup(
    name='sugar_core',
    version='3.0',
    description='Refactored C++ backend',
    ext_modules=ext_modules,
)