import os
import markdown
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QPushButton)
from PyQt5.QtCore import Qt
from utils import get_resource_path

class HelpWindow(QDialog):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.resize(700, 600)
        self.dark_mode = dark_mode
        
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.init_ui()
        self.load_help_text()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        
        layout.addWidget(self.text_browser)
        
        self.btn_close = QPushButton("Понятно")
        self.btn_close.clicked.connect(self.close)
        layout.addWidget(self.btn_close)

    def load_help_text(self):
        """
        Читает файл help.md (используя get_resource_path для совместимости с exe),
        конвертирует Markdown в HTML и добавляет CSS стили.
        """
        help_path = get_resource_path("help.md")
        
        try:
            with open(help_path, "r", encoding="utf-8") as f:
                md_text = f.read()
                
            html_content = markdown.markdown(md_text)
            
            if self.dark_mode:
                text_color = "#E0E0E0"
                header_color = "#4CAF50"
                link_color = "#81C784"
            else:
                text_color = "#000000"
                header_color = "#2196F3"
                link_color = "#1E88E5"

            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: sans-serif; 
                        color: {text_color}; 
                        margin: 20px; 
                    }}
                    h1 {{ 
                        color: {header_color}; 
                        border-bottom: 2px solid {header_color}; 
                        padding-bottom: 10px; 
                        font-size: 22px;
                    }}
                    h2 {{ 
                        color: {header_color}; 
                        margin-top: 25px; 
                        font-size: 18px;
                    }}
                    p, li {{ 
                        line-height: 1.6; 
                        font-size: 14px; 
                    }}
                    strong {{ 
                        color: {header_color}; 
                    }}
                    a {{ 
                        color: {link_color}; 
                        text-decoration: none; 
                    }}
                    blockquote {{ 
                        border-left: 4px solid {header_color}; 
                        margin-left: 0; 
                        padding-left: 15px; 
                        color: #999; 
                        font-style: italic;
                    }}
                    ul {{ padding-left: 20px; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            self.text_browser.setHtml(styled_html)
            
        except FileNotFoundError:
            self.text_browser.setText(f"<h3>Ошибка</h3><p>Файл справки не найден по пути:<br>{help_path}</p>")
        except Exception as e:
            self.text_browser.setText(f"<h3>Ошибка</h3><p>Не удалось прочитать справку:<br>{str(e)}</p>")

    def apply_theme(self):
        """Стилизация окна и виджетов."""
        if self.dark_mode:
            bg = "#282828"
            input_bg = "#333"
            acc = "#4CAF50"
            border = "#555"
        else:
            bg = "#F0F0F0"
            input_bg = "#FFFFFF"
            acc = "#2196F3"
            border = "#CCC"

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; }}
            
            QTextBrowser {{ 
                background-color: {input_bg}; 
                border: 1px solid {border}; 
                border-radius: 5px;
            }}
            
            QPushButton {{ 
                background-color: {acc}; 
                color: white; 
                border-radius: 5px; 
                padding: 10px; 
                font-weight: bold; 
            }}
            QPushButton:hover {{ background-color: {acc}CC; }}
        """)