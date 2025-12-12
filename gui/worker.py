import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os


class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    paused_state_saved = pyqtSignal(int, dict)

    def __init__(self, params, start_index=0, prev_strategies=None):
        super().__init__()
        self.params = params
        self.start_index = start_index
        if prev_strategies:
            self.strategies = prev_strategies
        else:
            self.strategies = {
                'greedy': [], 'thrifty': [], 'median': [],
                'greedy_thrifty': [], 'thrifty_greedy': []
            }

    def run(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            import sugar_core
            generator = sugar_core.MatrixGenerator(self.params)
            
            T = self.params['T']
            v_val = self.params.get('v', 0)
            
            for i in range(self.start_index, T):
                if self.isInterruptionRequested():
                    self.paused_state_saved.emit(i, self.strategies)
                    return 
                
                S_matrix = generator.generate()
                S_opt = sugar_core.solve_exact(S_matrix)
                
                if S_opt <= 1e-9: 
                    if i % max(1, T // 100) == 0:
                        self.progress_updated.emit(i + 1)
                    continue
                
                self.strategies['greedy'].append((S_opt - sugar_core.run_greedy(S_matrix)) / S_opt * 100.0)
                self.strategies['thrifty'].append((S_opt - sugar_core.run_thrifty(S_matrix)) / S_opt * 100.0)
                self.strategies['median'].append((S_opt - sugar_core.run_median(S_matrix)) / S_opt * 100.0)
                self.strategies['greedy_thrifty'].append((S_opt - sugar_core.run_greedy_thrifty(S_matrix, v_val)) / S_opt * 100.0)
                self.strategies['thrifty_greedy'].append((S_opt - sugar_core.run_thrifty_greedy(S_matrix, v_val)) / S_opt * 100.0)
                
                if i % max(1, T // 100) == 0:
                    self.progress_updated.emit(i + 1)
            
            if self.isInterruptionRequested():
                self.paused_state_saved.emit(T, self.strategies)
                return

            self.progress_updated.emit(T)

            if not self.strategies['greedy']:
                raise Exception("Все эксперименты выдали 0 сахара или были пропущены.")

            avg_losses = {name: np.mean(vals) for name, vals in self.strategies.items()}
            self.result_ready.emit(avg_losses)

        except ImportError as e:
            self.error_occurred.emit(f"Ошибка импорта C++ модуля: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Ошибка вычислений: {str(e)}")