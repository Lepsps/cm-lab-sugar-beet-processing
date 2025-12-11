import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QFormLayout, QCheckBox, 
                             QComboBox, QMessageBox, QProgressBar, QGroupBox, 
                             QTextEdit, QApplication, QMenu, QColorDialog, QToolButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Импорт потока вычислений
from gui.worker import WorkerThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("СППР: Переработка сахарной свеклы")
        self.setGeometry(100, 100, 1150, 800)
        
        # --- НАСТРОЙКИ ТЕМЫ ПО УМОЛЧАНИЮ ---
        self.dark_mode = True 
        self.bg_color = QColor(40, 40, 40)
        self.text_color = QColor(255, 255, 255)
        self.accent_color = QColor("#4CAF50")
        self.input_bg_color = QColor(60, 60, 60)
        
        self.worker = None
        self.last_results = {} 
        
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # --- ЛЕВАЯ ПАНЕЛЬ (Настройки) ---
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_panel.setFixedWidth(360)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(10)
        
        # Группы параметров
        grp_gen = QGroupBox("Общие параметры")
        form_gen = QFormLayout()
        self.inp_T = QLineEdit("50") 
        self.inp_n = QLineEdit("15")
        form_gen.addRow("Экспериментов (T):", self.inp_T)
        form_gen.addRow("Партий (n):", self.inp_n)
        grp_gen.setLayout(form_gen)
        settings_layout.addWidget(grp_gen)
        
        grp_params = QGroupBox("Параметры сырья")
        form_params = QFormLayout()
        self.inp_alpha_min = QLineEdit("0.12")
        self.inp_alpha_max = QLineEdit("0.22")
        self.inp_beta1 = QLineEdit("0.86") 
        self.inp_beta2 = QLineEdit("0.99")
        self.combo_dist = QComboBox()
        self.combo_dist.addItems(["Равномерно", "Концентрировано"])
        form_params.addRow("Alpha min:", self.inp_alpha_min)
        form_params.addRow("Alpha max:", self.inp_alpha_max)
        form_params.addRow("Beta 1:", self.inp_beta1)
        form_params.addRow("Beta 2:", self.inp_beta2)
        form_params.addRow("Распред.:", self.combo_dist)
        grp_params.setLayout(form_params)
        settings_layout.addWidget(grp_params)
        
        grp_rip = QGroupBox("Дозаривание")
        v_rip = QVBoxLayout()
        self.chk_ripening = QCheckBox("Учитывать дозаривание")
        self.chk_ripening.stateChanged.connect(self.toggle_ripening)
        form_rip = QFormLayout()
        self.inp_v = QLineEdit("7")
        self.inp_beta_max = QLineEdit("1.07")
        self.inp_v.setEnabled(False)
        self.inp_beta_max.setEnabled(False)
        form_rip.addRow("Этапов (v):", self.inp_v)
        form_rip.addRow("Beta max:", self.inp_beta_max)
        v_rip.addWidget(self.chk_ripening)
        v_rip.addLayout(form_rip)
        grp_rip.setLayout(v_rip)
        settings_layout.addWidget(grp_rip)
        
        grp_chem = QGroupBox("Химия")
        v_chem = QVBoxLayout()
        self.chk_chem = QCheckBox("Учитывать влияние (потери)")
        v_chem.addWidget(self.chk_chem)
        grp_chem.setLayout(v_chem)
        settings_layout.addWidget(grp_chem)
        
        # Кнопки
        self.btn_run = QPushButton("ЗАПУСТИТЬ МОДЕЛИРОВАНИЕ")
        self.btn_run.setFixedHeight(50)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_experiment)
        
        self.btn_cancel = QPushButton("ОТМЕНИТЬ")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.cancel_experiment)
        self.btn_cancel.hide()
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)
        
        settings_layout.addWidget(self.btn_run)
        settings_layout.addWidget(self.btn_cancel)
        settings_layout.addWidget(self.progress)
        
        settings_layout.addStretch()
        
        # Шестеренка
        self.btn_settings = QToolButton()
        self.btn_settings.setText("⚙") 
        self.btn_settings.setFixedSize(40, 40)
        font = QFont(); font.setPointSize(20)
        self.btn_settings.setFont(font)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setPopupMode(QToolButton.InstantPopup) 
        self.btn_settings.clicked.connect(self.open_settings_menu)
        
        settings_layout.addWidget(self.btn_settings)
        
        # --- ПРАВАЯ ПАНЕЛЬ (Результаты) ---
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        results_layout.addWidget(self.canvas)
        
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setMaximumHeight(150)
        self.txt_output.setPlaceholderText("Результаты появятся здесь...")
        results_layout.addWidget(self.txt_output)
        
        main_layout.addWidget(settings_panel)
        main_layout.addWidget(results_panel)

    def toggle_ripening(self, state):
        is_checked = (state == Qt.Checked)
        self.inp_v.setEnabled(is_checked)
        self.inp_beta_max.setEnabled(is_checked)

    def open_settings_menu(self):
        menu = QMenu(self)
        mode_text = "☀ Включить светлую тему" if self.dark_mode else "🌙 Включить темную тему"
        action_mode = menu.addAction(mode_text)
        action_mode.triggered.connect(self.toggle_dark_mode)
        menu.addSeparator()
        action_accent = menu.addAction("🎨 Цвет кнопок")
        action_accent.triggered.connect(self.choose_accent_color)
        action_bg = menu.addAction("🖼️ Цвет фона")
        action_bg.triggered.connect(self.choose_bg_color)
        menu.exec_(self.btn_settings.mapToGlobal(self.btn_settings.rect().topRight()))

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
        
        style = f"""
            QMainWindow {{ background-color: {bg}; }}
            QGroupBox {{ font-weight: bold; border: 1px solid {acc}; border-radius: 6px; margin-top: 12px; color: {acc};}}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
            QLineEdit, QComboBox {{ background-color: {inp}; color: {fg}; border: 1px solid #777; border-radius: 4px; padding: 5px;}}
            QLineEdit:focus {{ border: 2px solid {acc}; }}
            QProgressBar {{ border: 1px solid #777; border-radius: 6px; text-align: center; background-color: {inp}; color: {fg};}}
            QProgressBar::chunk {{ background-color: {acc}; border-radius: 5px; }}
            QTextEdit {{ background-color: {inp}; color: {fg}; border: 1px solid {acc}; border-radius: 6px; font-size: 13px;}}
            QPushButton {{ background-color: {acc}; color: {btn_fg}; border-radius: 6px; font-weight: bold; font-size: 14px; border: none;}}
            QPushButton:hover {{ background-color: {self.accent_color.lighter(110).name()}; }}
            QPushButton:pressed {{ background-color: {self.accent_color.darker(110).name()}; }}
            QPushButton:disabled {{ background-color: #555; color: #888; }}
            QToolButton {{ background-color: transparent; color: {fg}; border: none; border-radius: 20px;}}
            QToolButton:hover {{ background-color: rgba(128, 128, 128, 0.3); }}
            QMenu {{ background-color: {inp}; color: {fg}; border: 1px solid {acc}; }}
            QMenu::item:selected {{ background-color: {acc}; color: {btn_fg}; }}
        """
        self.setStyleSheet(style)
        self.btn_cancel.setStyleSheet(f"background-color: #D32F2F; color: white; border-radius: 6px; font-weight: bold;")
        self.plot_results(self.last_results)

    def validate_input(self, name, widget, min_val=-float('inf'), max_val=float('inf'), is_int=True):
        """Хелпер для детальной проверки полей ввода."""
        text = widget.text().strip().replace(',', '.') # Заменяем запятые на точки
        if not text:
            raise ValueError(f"Поле '{name}' не может быть пустым.")
        try:
            val = int(text) if is_int else float(text)
            if not (min_val <= val <= max_val):
                raise ValueError(f"Значение '{name}' должно быть в диапазоне [{min_val}, {max_val}].")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Некорректное число в поле '{name}'. Введено: '{text}'")

    def get_params(self):
        """Сбор и детальная валидация всех данных с формы."""
        try:
            p = {}
            p['T'] = self.validate_input("Экспериментов (T)", self.inp_T, min_val=1)
            p['n'] = self.validate_input("Партий (n)", self.inp_n, min_val=1)
            
            p['alpha_min'] = self.validate_input("Alpha min", self.inp_alpha_min, 0.0, 1.0, is_int=False)
            p['alpha_max'] = self.validate_input("Alpha max", self.inp_alpha_max, 0.0, 1.0, is_int=False)
            if p['alpha_min'] > p['alpha_max']: raise ValueError("Alpha min не может быть больше Alpha max.")

            p['beta1'] = self.validate_input("Beta 1", self.inp_beta1, 0.0, 1.0, is_int=False)
            p['beta2'] = self.validate_input("Beta 2", self.inp_beta2, 0.0, 1.0, is_int=False)
            if p['beta1'] > p['beta2']: raise ValueError("Beta 1 не может быть больше Beta 2.")
            
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
            QMessageBox.critical(self, "Ошибка ввода", str(e))
            return None

    def start_experiment(self):
        params = self.get_params()
        if not params: return
        
        self.btn_run.hide()
        self.btn_cancel.show()
        self.txt_output.clear()
        self.progress.setMaximum(params['T'])
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        
        self.worker = WorkerThread(params)
        self.worker.progress_updated.connect(self.progress.setValue)
        self.worker.result_ready.connect(self.display_results)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def cancel_experiment(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.txt_output.append("\n... Отменяется, ждем завершения ...")
            self.btn_cancel.setEnabled(False)

    def on_worker_finished(self):
        self.btn_cancel.hide()
        self.btn_cancel.setEnabled(True)
        self.btn_run.show()
        if self.worker and self.worker.isInterruptionRequested():
            self.txt_output.append("\nПроцесс был отменен.")
            self.progress.setValue(0) 
            self.progress.setFormat("Отменено")

    def handle_error(self, msg):
        self.btn_cancel.hide()
        self.btn_cancel.setEnabled(True)
        self.btn_run.show()
        self.progress.setValue(0) 
        self.progress.setFormat("Ошибка")
        QMessageBox.critical(self, "Ошибка", msg)

    def display_results(self, avg_losses):
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

    def plot_results(self, avg_losses):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        bg_hex, fg_hex = self.bg_color.name(), self.text_color.name()
        
        self.figure.patch.set_facecolor(bg_hex)
        ax.set_facecolor(bg_hex)
        
        labels = ['Жадная', 'Бережл.', 'Ж-Б', 'Б-Ж', 'Медиана']
        keys = ['greedy', 'thrifty', 'greedy_thrifty', 'thrifty_greedy', 'median']
        values = [avg_losses.get(k, 0) for k in keys]
        
        bar_colors = ['#808080', '#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#C2C2F0']
        bars = ax.bar(labels, values, color=bar_colors)
        
        ax.tick_params(axis='x', colors=fg_hex)
        ax.tick_params(axis='y', colors=fg_hex)
        for spine in ax.spines.values(): spine.set_color(fg_hex)
        
        ax.set_ylabel('Потери (%)', color=fg_hex)
        ax.set_title('Сравнение эффективности стратегий', color=fg_hex)
        ax.grid(axis='y', linestyle='--', alpha=0.3, color=fg_hex)
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}%', 
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', color=fg_hex, fontweight='bold')
        self.canvas.draw()