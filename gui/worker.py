import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os
import traceback

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            # Импорт C++ модуля
            current_dir = os.getcwd()
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            import sugar_core

            generator = sugar_core.MatrixGenerator(self.params)
            
            strategies = {
                'greedy': [], 'thrifty': [], 'median': [],
                'greedy_thrifty': [], 'thrifty_greedy': []
            }
            
            T = self.params['T']
            v_val = self.params.get('v', 0)
            valid_experiments = 0
            
            for i in range(T):
                # --- Проверка на отмену ---
                if self.isInterruptionRequested():
                    return # Безопасно выходим из цикла и потока
                
                S_matrix = generator.generate()
                S_opt = sugar_core.solve_exact(S_matrix)
                
                if S_opt <= 1e-9: 
                    continue
                
                valid_experiments += 1
                
                # Расчет стратегий
                strategies['greedy'].append((S_opt - sugar_core.run_greedy(S_matrix)) / S_opt * 100.0)
                strategies['thrifty'].append((S_opt - sugar_core.run_thrifty(S_matrix)) / S_opt * 100.0)
                strategies['median'].append((S_opt - sugar_core.run_median(S_matrix)) / S_opt * 100.0)
                strategies['greedy_thrifty'].append((S_opt - sugar_core.run_greedy_thrifty(S_matrix, v_val)) / S_opt * 100.0)
                strategies['thrifty_greedy'].append((S_opt - sugar_core.run_thrifty_greedy(S_matrix, v_val)) / S_opt * 100.0)
                
                if i % max(1, T // 100) == 0:
                    self.progress_updated.emit(i + 1)
            
            if self.isInterruptionRequested(): return

            self.progress_updated.emit(T)

            if valid_experiments == 0:
                raise Exception("Все эксперименты выдали 0 сахара. Проверьте параметры.")

            # Усреднение
            avg_losses = {name: np.mean(vals) if vals else 0.0 for name, vals in strategies.items()}
            self.result_ready.emit(avg_losses)

        except ImportError as e:
            self.error_occurred.emit(f"Не удалось загрузить C++ модуль 'sugar_core'.\n\nДетали: {str(e)}\n\nУбедитесь, что файл .pyd лежит рядом с main.py и версия Python совпадает.")
        except Exception as e:
            self.error_occurred.emit(str(e) + "\n\nСмотрите консоль для деталей.")