import os
import sys
import subprocess
import glob
import shutil

def install_requirements():
    print("--- [1/4] Проверка и установка зависимостей ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "markdown", "pybind11"])

def build_cpp_extension():
    print("--- [2/4] Компиляция C++ ядра в папку build ---")
    
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    os.makedirs("build")
    
    cmd = [sys.executable, "setup.py", "build_ext", "--build-lib=build"]
    print("Выполняем:", " ".join(cmd))
    subprocess.check_call(cmd)

def find_pyd_file():
    search_pattern = os.path.join("build", "sugar_core*.pyd")
    pyd_files = glob.glob(search_pattern) + glob.glob(os.path.join("build", "sugar_core*.so"))
    
    if not pyd_files:
        raise FileNotFoundError("Ошибка: Файл .pyd не найден в папке build.")
    
    return os.path.abspath(pyd_files[0])

def run_pyinstaller(pyd_file):
    print(f"--- [3/4] Сборка EXE с помощью PyInstaller ---")
    
    help_file = os.path.abspath("help.md")
    
    icon_path = os.path.abspath(os.path.join("assets", "icon.ico"))
    
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"❌ ОШИБКА: Файл иконки не найден! Проверьте путь: {icon_path}")
    
    if not os.path.exists(help_file):
        raise FileNotFoundError(f"Файл справки не найден: {help_file}")

    sep = ";" if os.name == 'nt' else ":"
    
    add_data_help = f"--add-data={help_file}{sep}."
    add_data_icon = f"--add-data={icon_path}{sep}assets"

    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name=SugarBeet Optimizer",
        "--distpath=.",         
        "--specpath=build",     
        "--workpath=build",     
        
        add_data_help,
        add_data_icon,
        
        f"--add-binary={pyd_file}{sep}.",
        f"--icon={icon_path}",
        
        "--hidden-import=sugar_core",
        "--exclude-module=PIL._avif",
        "--collect-all=PIL",       
        "--clean",
        "main.py"
    ]
    
    print("Выполняем команду:", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    try:
        install_requirements()
        build_cpp_extension()
        pyd_file = find_pyd_file()
        run_pyinstaller(pyd_file)
        
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        
        print("\n===========================================")
        print("✅ СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
        print(f"Готовый файл: {os.path.abspath('SugarBeet Optimizer.exe')}")
        print("Временные файлы спрятаны в папке build/")
        print("===========================================")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА СБОРКИ: {e}")
        input("Нажмите Enter, чтобы выйти...")

if __name__ == "__main__":
    main()