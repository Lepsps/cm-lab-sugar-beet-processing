from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QPushButton, 
                             QMenu, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
import data.database as db

class HistoryWindow(QDialog):
    experiment_selected = pyqtSignal(dict, dict)

    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.setWindowTitle("История экспериментов")
        self.resize(750, 500)
        self.dark_mode = dark_mode
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()
        self.load_data()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.lbl_info = QLabel("Дважды кликните по строке, чтобы загрузить параметры и результаты.")
        layout.addWidget(self.lbl_info)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Время", "Параметры эксперимента"])
        
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.setFocusPolicy(Qt.NoFocus)
        
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        
        self.btn_clear = QPushButton("Очистить историю...")
        self.btn_clear.clicked.connect(self.show_clear_menu)
        
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        records = db.get_all_records()
        self.table.setRowCount(len(records))
        self.records_data = records 

        for row, rec in enumerate(records):
            p = rec['params']
            
            dist_char = "Равн." if p.get('dist_type') == 'uniform' else "Конц."
            chem_char = "Есть" if p.get('use_inorganic') else "Нет"
            rip_char = f"Да(v={p.get('v')})" if p.get('use_ripening') else "Нет"
            
            desc = (f"T={p.get('T')}, n={p.get('n')} | "
                    f"α=[{p.get('alpha_min')}-{p.get('alpha_max')}] | "
                    f"β=[{p.get('beta1')}-{p.get('beta2')}] | Распред: {dist_char}"
                    f"Дозар: {rip_char}, Хим: {chem_char}")
            
            item_id = QTableWidgetItem(str(rec['id']))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_time = QTableWidgetItem(rec['timestamp'])
            item_desc = QTableWidgetItem(desc)
            
            self.table.setItem(row, 0, item_id)
            self.table.setItem(row, 1, item_time)
            self.table.setItem(row, 2, item_desc)

    def on_row_double_clicked(self, row, column):
        record = self.records_data[row]
        self.experiment_selected.emit(record['params'], record['results'])
        self.close()

    def show_clear_menu(self):
        """Показывает меню с вариантами очистки."""
        menu = QMenu(self)
        
        if self.dark_mode:
            menu.setStyleSheet("""
                QMenu { background-color: #3C3C3C; color: white; border: 1px solid #555; }
                QMenu::item { padding: 5px 20px; }
                QMenu::item:selected { background-color: #4CAF50; color: white; }
            """)
        else:
            menu.setStyleSheet("""
                QMenu { background-color: white; color: black; border: 1px solid #CCC; }
                QMenu::item { padding: 5px 20px; }
                QMenu::item:selected { background-color: #2196F3; color: white; }
            """)

        act_30m = menu.addAction("За последние 30 минут")
        act_24h = menu.addAction("За последний день (24ч)")
        menu.addSeparator()
        act_all = menu.addAction("Удалить ВСЮ историю")
        
        act_30m.triggered.connect(lambda: self.execute_clear("30m"))
        act_24h.triggered.connect(lambda: self.execute_clear("24h"))
        act_all.triggered.connect(lambda: self.execute_clear("all"))
        
        menu.exec_(self.btn_clear.mapToGlobal(self.btn_clear.rect().bottomLeft()))

    def execute_clear(self, mode):
        if mode == "30m":
            db.delete_last_minutes(30)
        elif mode == "24h":
            db.delete_last_minutes(24 * 60)
        elif mode == "all":
            confirm = QMessageBox.question(self, "Подтверждение", 
                                           "Вы действительно хотите удалить ВСЮ историю?",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return
            db.delete_all()
        
        self.load_data()

    def apply_theme(self):
        if self.dark_mode:
            bg = "#282828"
            fg = "#FFFFFF"
            input_bg = "#3C3C3C"
            acc = "#4CAF50"
            border = "#555"
        else:
            bg = "#F0F0F0"
            fg = "#000000"
            input_bg = "#FFFFFF"
            acc = "#2196F3"
            border = "#CCC"

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {fg}; }}
            QLabel {{ color: {fg}; font-size: 12px; margin-bottom: 5px; }}
            
            QTableWidget {{ 
                background-color: {input_bg}; 
                color: {fg}; 
                border: 1px solid {acc}; 
                gridline-color: {border}; 
            }}
            
            /* Стили кнопок */
            QPushButton {{ 
                background-color: {acc}; 
                color: white; 
                border-radius: 5px; 
                padding: 8px; 
                font-weight: bold; 
                min-width: 80px;
            }}
            QPushButton:hover {{ background-color: {acc}CC; }}
            
            QPushButton[text^="Очистить"] {{
                background-color: #D32F2F;
            }}
            QPushButton[text^="Очистить"]:hover {{
                background-color: #B71C1C;
            }}
        """)