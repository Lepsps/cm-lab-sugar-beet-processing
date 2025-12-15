import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QFormLayout, QCheckBox, 
                             QComboBox, QMessageBox, QProgressBar, QGroupBox, 
                             QTextEdit, QApplication, QMenu, QColorDialog, QToolButton,
                             QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import data.database as db
from gui.history_window import HistoryWindow
from gui.help_window import HelpWindow

try:
    from gui.worker import WorkerThread
except ImportError:
    from worker import WorkerThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("СППР: Переработка сахарной свеклы")
        
        # Размер окна
        self.setGeometry(100, 100, 1200, 800)
        
        # Базовый шрифт
        font = QFont()
        font.setPointSize(12) 
        self.setFont(font)

        db.init_db()
        
        self.dark_mode = True 
        self.bg_color = QColor(40, 40, 40)
        self.text_color = QColor(255, 255, 255)
        self.accent_color = QColor("#4CAF50")
        self.input_bg_color = QColor(60, 60, 60)
        
        self.worker = None
        self.last_results = {}
        
        self.resume_state = None      
        self.last_run_params = None   
        
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10) 
        main_layout.setSpacing(15) 
        
        # --- ЛЕВАЯ ПАНЕЛЬ ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(500) 
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        settings_content = QWidget()
        settings_layout = QVBoxLayout(settings_content)
        settings_layout.setContentsMargins(5, 0, 15, 0)
        settings_layout.setSpacing(15)
        
        # 1. Общие параметры
        grp_gen = QGroupBox("Общие параметры")
        form_gen = QFormLayout()
        form_gen.setVerticalSpacing(10)
        
        self.inp_T = QLineEdit("50") 
        self.inp_n = QLineEdit("15")
        self.inp_T.setMinimumHeight(38)
        self.inp_n.setMinimumHeight(38)

        form_gen.addRow("Экспериментов (T):", self.inp_T)
        form_gen.addRow("Партий (n):", self.inp_n)
        grp_gen.setLayout(form_gen)
        settings_layout.addWidget(grp_gen)
        
        # 2. Параметры сырья
        grp_params = QGroupBox("Параметры сырья")
        form_params = QFormLayout()
        form_params.setVerticalSpacing(10)

        self.inp_alpha_min = QLineEdit("0.12")
        self.inp_alpha_max = QLineEdit("0.22")
        self.inp_beta1 = QLineEdit("0.86") 
        self.inp_beta2 = QLineEdit("0.99")
        self.combo_dist = QComboBox()
        self.combo_dist.addItems(["Равномерно", "Концентрировано"])
        
        for w in [self.inp_alpha_min, self.inp_alpha_max, self.inp_beta1, self.inp_beta2, self.combo_dist]:
            w.setMinimumHeight(38) 

        form_params.addRow("Alpha min:", self.inp_alpha_min)
        form_params.addRow("Alpha max:", self.inp_alpha_max)
        form_params.addRow("Beta 1:", self.inp_beta1)
        form_params.addRow("Beta 2:", self.inp_beta2)
        form_params.addRow("Распред.:", self.combo_dist)
        grp_params.setLayout(form_params)
        settings_layout.addWidget(grp_params)
        
        # 3. Дозаривание
        grp_rip = QGroupBox("Дозаривание")
        v_rip = QVBoxLayout()
        self.chk_ripening = QCheckBox("Учитывать дозаривание")
        self.chk_ripening.setStyleSheet("QCheckBox::indicator { width: 24px; height: 24px; }")
        
        self.chk_ripening.stateChanged.connect(self.toggle_ripening)
        
        form_rip = QFormLayout()
        form_rip.setVerticalSpacing(10)
        self.inp_v = QLineEdit("7")
        self.inp_beta_max = QLineEdit("1.07")
        self.inp_v.setEnabled(False)
        self.inp_beta_max.setEnabled(False)
        self.inp_v.setMinimumHeight(38)
        self.inp_beta_max.setMinimumHeight(38)

        form_rip.addRow("Этапов (v):", self.inp_v)
        form_rip.addRow("Beta max:", self.inp_beta_max)
        v_rip.addWidget(self.chk_ripening)
        v_rip.addLayout(form_rip)
        grp_rip.setLayout(v_rip)
        settings_layout.addWidget(grp_rip)
        
        # 4. Химия
        grp_chem = QGroupBox("Химия")
        v_chem = QVBoxLayout()
        self.chk_chem = QCheckBox("Учитывать влияние (потери)")
        self.chk_chem.setStyleSheet("QCheckBox::indicator { width: 24px; height: 24px; }")
        v_chem.addWidget(self.chk_chem)
        grp_chem.setLayout(v_chem)
        settings_layout.addWidget(grp_chem)
        
        # Кнопки управления
        self.btn_run = QPushButton("ЗАПУСТИТЬ МОДЕЛИРОВАНИЕ")
        self.btn_run.setFixedHeight(55) 
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_experiment)
        
        self.btn_cancel = QPushButton("ОТМЕНИТЬ")
        self.btn_cancel.setFixedHeight(45) 
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.cancel_experiment)
        self.btn_cancel.hide()
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(30)
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)
        
        settings_layout.addWidget(self.btn_run)
        settings_layout.addWidget(self.btn_cancel)
        settings_layout.addWidget(self.progress)
        
        settings_layout.addStretch()
        
        # Кнопка настроек
        self.btn_settings = QToolButton()
        self.btn_settings.setText("⚙") 
        self.btn_settings.setFixedSize(55, 55)
        font_gear = QFont(); font_gear.setPointSize(26)
        self.btn_settings.setFont(font_gear)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setPopupMode(QToolButton.InstantPopup) 
        self.btn_settings.clicked.connect(self.open_settings_menu)
        
        settings_layout.addWidget(self.btn_settings)
        
        scroll_area.setWidget(settings_content)
        
        # --- ПРАВАЯ ПАНЕЛЬ (РЕЗУЛЬТАТЫ) ---
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        results_layout.addWidget(self.canvas)
        
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setMaximumHeight(220)
        self.txt_output.setPlaceholderText("Результаты появятся здесь...")
        results_layout.addWidget(self.txt_output)
        
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(results_panel)

    def toggle_ripening(self, state):
        is_checked = (state == Qt.Checked)
        self.inp_v.setEnabled(is_checked)
        self.inp_beta_max.setEnabled(is_checked)

    # --- ВАЛИДАЦИЯ ---
    def validate_input(self, name, widget, min_val=-float('inf'), max_val=float('inf'), is_int=True):
        text = widget.text().strip().replace(',', '.')
        if not text: raise ValueError(f"Неверный формат данных! Поле '{name}' не может быть пустым.")
        try:
            val = int(text) if is_int else float(text)
        except ValueError:
            type_str = "целое" if is_int else "числовое"
            raise ValueError(f"Неверный формат данных! Введите {type_str} число в поле '{name}'.")
        if not (min_val <= val <= max_val):
            if is_int and min_val == 1 and val <= 0:
                raise ValueError(f"Неверный формат данных! Введите целое положительное число (минимум 1) в поле '{name}'.")
            raise ValueError(f"Неверное значение в поле '{name}'!\nДопустимый диапазон: от {min_val} до {max_val}.")
        return val

    def get_params(self):
        try:
            p = {}
            p['T'] = self.validate_input("Экспериментов (T)", self.inp_T, min_val=1)
            p['n'] = self.validate_input("Партий (n)", self.inp_n, min_val=1)
            p['alpha_min'] = self.validate_input("Alpha min", self.inp_alpha_min, 0.0, 1.0, is_int=False)
            p['alpha_max'] = self.validate_input("Alpha max", self.inp_alpha_max, 0.0, 1.0, is_int=False)
            if p['alpha_min'] > p['alpha_max']: raise ValueError("Ошибка логики: Alpha min не может быть больше Alpha max.")
            p['beta1'] = self.validate_input("Beta 1", self.inp_beta1, 0.0, 1.0, is_int=False)
            p['beta2'] = self.validate_input("Beta 2", self.inp_beta2, 0.0, 1.0, is_int=False)
            if p['beta1'] > p['beta2']: raise ValueError("Ошибка логики: Beta 1 не может быть больше Beta 2.")
            p['dist_type'] = 'uniform' if self.combo_dist.currentIndex() == 0 else 'concentrated'
            p['use_ripening'] = self.chk_ripening.isChecked()
            if p['use_ripening']:
                p['v'] = self.validate_input("Этапов (v)", self.inp_v, 1, p['n'])
                p['beta_max'] = self.validate_input("Beta max", self.inp_beta_max, 1.0, float('inf'), is_int=False)
            else:
                p['v'], p['beta_max'] = 0, 1.0
            p['use_inorganic'] = self.chk_chem.isChecked()
            return p
        except ValueError as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка ввода")
            msg.setText(str(e))
            font = QFont(); font.setPointSize(16)
            msg.setFont(font)
            msg.exec_()
            return None

    # --- УПРАВЛЕНИЕ ПОТОКОМ ---
    def start_experiment(self):
        params = self.get_params()
        if not params: return
        start_idx = 0
        prev_data = None
        if self.resume_state and self.last_run_params == params:
            start_idx, prev_data = self.resume_state
            if start_idx >= params['T']:
                start_idx = 0
                prev_data = None
        else:
            self.resume_state = None
            self.last_run_params = params
        self.btn_run.hide()
        self.btn_cancel.show()
        if start_idx == 0:
            self.txt_output.clear()
            self.progress.setValue(0)
        self.progress.setMaximum(params['T'])
        self.progress.setFormat("%p%")
        self.worker = WorkerThread(params, start_index=start_idx, prev_strategies=prev_data)
        self.worker.progress_updated.connect(self.progress.setValue)
        self.worker.result_ready.connect(self.display_results)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.paused_state_saved.connect(self.save_state_on_pause)
        self.worker.start()

    def cancel_experiment(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.btn_cancel.setEnabled(False)

    def save_state_on_pause(self, idx, data):
        self.resume_state = (idx, data)
        self.progress.setFormat(f"Пауза ({idx}/{self.last_run_params['T']})")

    def on_worker_finished(self):
        self.btn_cancel.hide()
        self.btn_cancel.setEnabled(True)
        self.btn_run.show()
        if self.worker and self.worker.isInterruptionRequested():
            self.btn_run.setText("ПРОДОЛЖИТЬ")
        else:
            self.btn_run.setText("ЗАПУСТИТЬ МОДЕЛИРОВАНИЕ")

    def handle_error(self, msg_text):
        self.btn_cancel.hide()
        self.btn_cancel.setEnabled(True)
        self.btn_run.show()
        self.progress.setValue(0) 
        self.progress.setFormat("Ошибка")
        self.resume_state = None
        self.last_run_params = None
        self.btn_run.setText("ЗАПУСТИТЬ МОДЕЛИРОВАНИЕ")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Критическая ошибка")
        msg.setText(msg_text)
        msg.setFont(QFont("Arial", 16))
        msg.exec_()

    def display_results(self, avg_losses):
        self.resume_state = None 
        self.btn_run.setText("ЗАПУСТИТЬ МОДЕЛИРОВАНИЕ")
        if self.last_run_params:
            db.add_record(self.last_run_params, avg_losses)
        self.last_results = avg_losses
        self.plot_results(avg_losses)
        report = "=== РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА ===\n\n"
        names_ru = {'greedy': 'Жадная', 'thrifty': 'Бережливая',
                    'greedy_thrifty': 'Жадно-бережливая',
                    'thrifty_greedy': 'Бережливо-жадная', 'median': 'Медианная'}
        if avg_losses:
            sorted_res = sorted(avg_losses.items(), key=lambda item: item[1])
            for name, val in sorted_res:
                report += f"{names_ru[name]:<20} : {val:.2f}% потерь\n"
            best_strat = sorted_res[0][0]
            report += f"\n🏆 РЕКОМЕНДУЕМАЯ СТРАТЕГИЯ: {names_ru[best_strat].upper()}"
        else:
            report += "Нет данных для отображения."
        self.txt_output.setText(report)

    # --- ГРАФИКИ (С УВЕЛИЧЕННЫМ ОТСТУПОМ) ---
    def plot_results(self, avg_losses):
        self.ax.clear()
        bg_hex, fg_hex = self.bg_color.name(), self.text_color.name()
        self.figure.patch.set_facecolor(bg_hex)
        self.ax.set_facecolor(bg_hex)
        labels = ['Жадная', 'Бережл.', 'Ж-Б', 'Б-Ж', 'Медиана']
        keys = ['greedy', 'thrifty', 'greedy_thrifty', 'thrifty_greedy', 'median']
        values = [avg_losses.get(k, 0) for k in keys]
        bar_colors = ['#808080', '#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#C2C2F0']
        
        # --- ЛОГИКА УВЕЛИЧЕНИЯ ОТСТУПА СВЕРХУ ---
        max_val = max(values) if values else 0
        if max_val > 0:
            self.ax.set_ylim(0, max_val * 1.2)
        else:
            self.ax.set_ylim(0, 10)

        bars = self.ax.bar(labels, values, color=bar_colors)
        
        self.ax.tick_params(axis='x', colors=fg_hex, labelsize=12)
        self.ax.tick_params(axis='y', colors=fg_hex, labelsize=12)
        for spine in self.ax.spines.values(): spine.set_color(fg_hex)
        
        self.ax.set_ylabel('Потери (%)', color=fg_hex, fontsize=14)
        self.ax.set_title('Сравнение эффективности стратегий', color=fg_hex, fontsize=16, pad=12)
        self.ax.grid(axis='y', linestyle='--', alpha=0.3, color=fg_hex)
        
        for bar in bars:
            height = bar.get_height()
            self.ax.annotate(f'{height:.2f}%', 
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', color=fg_hex, 
                        fontweight='bold', fontsize=12)
        
        self.figure.tight_layout()
        self.canvas.draw()

    # --- МЕНЮ ---
    def open_settings_menu(self):
        menu = QMenu(self)
        action_history = menu.addAction("📜 История запросов")
        action_history.triggered.connect(self.show_history)
        action_help = menu.addAction("❓ Помощь")
        action_help.triggered.connect(self.show_help)
        menu.addSeparator()
        mode_text = "☀ Включить светлую тему" if self.dark_mode else "🌙 Включить темную тему"
        action_mode = menu.addAction(mode_text)
        action_mode.triggered.connect(self.toggle_dark_mode)
        menu.addSeparator()
        action_accent = menu.addAction("🎨 Цвет кнопок")
        action_accent.triggered.connect(self.choose_accent_color)
        action_bg = menu.addAction("🖼️ Цвет фона")
        action_bg.triggered.connect(self.choose_bg_color)
        menu.exec_(self.btn_settings.mapToGlobal(self.btn_settings.rect().topRight()))

    def show_history(self):
        self.history_window = HistoryWindow(self, self.dark_mode)
        self.history_window.experiment_selected.connect(self.load_from_history)
        self.history_window.exec_()

    def show_help(self):
        self.help_window = HelpWindow(self, self.dark_mode)
        self.help_window.exec_()

    def load_from_history(self, params, results):
        self.inp_T.setText(str(params.get('T')))
        self.inp_n.setText(str(params.get('n')))
        self.inp_alpha_min.setText(str(params.get('alpha_min')))
        self.inp_alpha_max.setText(str(params.get('alpha_max')))
        self.inp_beta1.setText(str(params.get('beta1')))
        self.inp_beta2.setText(str(params.get('beta2')))
        idx = 0 if params.get('dist_type') == 'uniform' else 1
        self.combo_dist.setCurrentIndex(idx)
        self.chk_ripening.setChecked(params.get('use_ripening', False))
        if params.get('use_ripening'):
            self.inp_v.setText(str(params.get('v')))
            self.inp_beta_max.setText(str(params.get('beta_max')))
        self.chk_chem.setChecked(params.get('use_inorganic', False))
        self.last_run_params = params 
        self.progress.setValue(100)
        self.progress.setFormat("Из истории")
        self.display_results(results)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.bg_color, self.accent_color = QColor(40, 40, 40), QColor("#4CAF50")
        else:
            self.bg_color, self.accent_color = QColor(240, 240, 240), QColor("#2196F3")
        self.update_theme_colors()
        self.apply_theme()

    def choose_accent_color(self):
        color = QColorDialog.getColor(self.accent_color, self, "Цвет кнопок")
        if color.isValid():
            self.accent_color = color
            self.apply_theme()

    def choose_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Цвет фона")
        if color.isValid():
            self.bg_color = color
            self.update_theme_colors()
            self.apply_theme()

    def update_theme_colors(self):
        if self.bg_color.lightness() < 128:
            self.text_color, self.input_bg_color = QColor(255, 255, 255), self.bg_color.lighter(150)
        else:
            self.text_color, self.input_bg_color = QColor(0, 0, 0), QColor(255, 255, 255)

    def apply_theme(self):
        app = QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.Window, self.bg_color)
        palette.setColor(QPalette.WindowText, self.text_color)
        palette.setColor(QPalette.Base, self.input_bg_color)
        palette.setColor(QPalette.Text, self.text_color)
        palette.setColor(QPalette.Button, self.bg_color)
        palette.setColor(QPalette.ButtonText, self.text_color)
        palette.setColor(QPalette.Highlight, self.accent_color)
        app.setPalette(palette)

        bg, fg, inp, acc = self.bg_color.name(), self.text_color.name(), self.input_bg_color.name(), self.accent_color.name()
        btn_fg = "white" if self.accent_color.lightness() < 180 else "black"
        msg_bg = inp if self.dark_mode else "white"
        msg_fg = fg
        scroll_bg = bg
        
        style = f"""
            QMainWindow {{ background-color: {bg}; }}
            
            QScrollArea {{ border: none; background-color: {scroll_bg}; }}
            QScrollArea > QWidget > QWidget {{ background-color: {scroll_bg}; }}
            
            QGroupBox {{ 
                font-weight: bold; 
                font-size: 24px; 
                border: 2px solid {acc}; 
                border-radius: 8px; 
                margin-top: 12px; 
                color: {acc};
                padding-top: 15px; 
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
            
            QLabel {{ font-size: 21px; }} 
            
            QLineEdit, QComboBox {{ 
                background-color: {inp}; 
                color: {fg}; 
                border: 2px solid #777; 
                border-radius: 6px; 
                padding: 5px;
                font-size: 21px; 
            }}
            QLineEdit:focus {{ border: 3px solid {acc}; }}
            QLineEdit:disabled {{ color: #777; border-color: #555; }}
            
            QProgressBar {{ 
                border: 2px solid #777; 
                border-radius: 8px; 
                text-align: center; 
                background-color: {inp}; 
                color: {fg};
                font-size: 16px;
            }}
            QProgressBar::chunk {{ background-color: {acc}; border-radius: 6px; }}
            
            QTextEdit {{ 
                background-color: {inp}; 
                color: {fg}; 
                border: 2px solid {acc}; 
                border-radius: 8px; 
                font-size: 21px; 
            }}
            
            QPushButton {{ 
                background-color: {acc}; 
                color: {btn_fg}; 
                border-radius: 8px; 
                font-weight: bold; 
                font-size: 18px; 
                border: none;
            }}
            QPushButton:hover {{ background-color: {self.accent_color.lighter(110).name()}; }}
            QPushButton:pressed {{ background-color: {self.accent_color.darker(110).name()}; }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
            
            QToolButton {{ background-color: transparent; color: {fg}; border: none; border-radius: 25px;}}
            QToolButton:hover {{ background-color: rgba(128, 128, 128, 0.3); }}
            
            QMenu {{ 
                background-color: {inp}; 
                color: {fg}; 
                border: 2px solid {acc}; 
                font-size: 16px; 
            }}
            QMenu::item {{ padding: 8px 25px; }}
            QMenu::item:selected {{ background-color: {acc}; color: {btn_fg}; }}
            
            QMessageBox {{ background-color: {msg_bg}; }}
            QMessageBox QLabel {{ color: {msg_fg}; font-size: 18px; }}
            QMessageBox QPushButton {{ width: 90px; height: 35px; font-size: 16px; }}
            QCheckBox {{ font-size: 21px; color: {fg}; spacing: 10px; }} 
        """
        self.setStyleSheet(style)
        self.btn_cancel.setStyleSheet(f"background-color: #D32F2F; color: white; border-radius: 8px; font-weight: bold; font-size: 18px;")
        
        if self.last_results:
            self.plot_results(self.last_results)
        else:
            self.figure.patch.set_facecolor(bg)
            self.ax.set_facecolor(bg)
            self.canvas.draw()