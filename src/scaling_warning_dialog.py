# scaling_warning_dialog.py
import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from language_manager import LanguageManager, language_manager

class ScalingWarningDialog(QDialog):
    def __init__(self, scaling_percentage):
        super().__init__()
        self.scaling_percentage = scaling_percentage
        self.language_manager = language_manager  # 使用全局實例
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(self.language_manager.get_text("scaling_warning_title", "⚠️ 系統設定問題"))
        self.setFixedSize(650, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton#languageButton {
                background-color: #28a745;
                min-width: 80px;
            }
            QPushButton#languageButton:hover {
                background-color: #218838;
            }
            QPushButton#closeButton {
                background-color: #dc3545;
                min-width: 120px;
            }
            QPushButton#closeButton:hover {
                background-color: #c82333;
            }
            QTextEdit {
                background-color: #363636;
                color: #ffffff;
                border: 1px solid #555555;
                font-size: 11px;
                font-family: 'Courier New', monospace;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 語言切換按鈕
        language_layout = QHBoxLayout()
        language_layout.addStretch()
        self.language_button = QPushButton()
        self.language_button.setObjectName("languageButton")
        self.language_button.clicked.connect(self.toggle_language)
        language_layout.addWidget(self.language_button)
        layout.addLayout(language_layout)
        
        # 標題
        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #ff6b6b; margin: 10px 0;")
        layout.addWidget(self.title_label)
        
        # 問題說明
        self.problem_label = QLabel()
        self.problem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.problem_label.setStyleSheet("color: #ffd93d; font-size: 14px; margin: 5px 0;")
        layout.addWidget(self.problem_label)
        
        self.explanation_label = QLabel()
        self.explanation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.explanation_label.setStyleSheet("color: #ffffff; font-size: 12px; margin: 10px 0;")
        layout.addWidget(self.explanation_label)
        
        # 修改教學
        self.tutorial_label = QLabel()
        self.tutorial_label.setStyleSheet("color: #4ecdc4; font-size: 14px; font-weight: bold; margin: 15px 0 5px 0;")
        layout.addWidget(self.tutorial_label)
        
        self.tutorial_text = QTextEdit()
        self.tutorial_text.setReadOnly(True)
        self.tutorial_text.setMaximumHeight(280)
        layout.addWidget(self.tutorial_text)
        
        # 按鈕
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton()
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.close_program)
        
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 初始化文本
        self.update_texts()
        
    def toggle_language(self):
        """切換語言"""
        current_lang = self.language_manager.get_current_language()
        new_lang = "en" if current_lang == "zh_tw" else "zh_tw"
        self.language_manager.set_language(new_lang)
        self.update_texts()
        
    def update_texts(self):
        """更新所有文本內容"""
        current_lang = self.language_manager.get_current_language()
        
        # 更新語言切換按鈕文本
        if current_lang == "zh_tw":
            self.language_button.setText("English")
        else:
            self.language_button.setText("中文")
        
        # 更新窗口標題
        self.setWindowTitle(self.language_manager.get_text("scaling_warning_title"))
        
        # 更新標題
        self.title_label.setText(self.language_manager.get_text("scaling_warning_main_title"))
        
        # 更新問題說明
        problem_text = self.language_manager.get_text("scaling_current_setting").format(self.scaling_percentage)
        self.problem_label.setText(problem_text)
        
        self.explanation_label.setText(self.language_manager.get_text("scaling_explanation"))
        
        # 更新教學標題
        self.tutorial_label.setText(self.language_manager.get_text("scaling_tutorial_title"))
        
        # 更新教學內容
        tutorial_content = self.language_manager.get_text("scaling_tutorial_content")
        self.tutorial_text.setPlainText(tutorial_content)
        
        # 更新關閉按鈕
        self.close_button.setText(self.language_manager.get_text("scaling_close_button"))
        
    def close_program(self):
        """關閉程序"""
        self.accept()
        QApplication.quit()
        sys.exit(0)

def check_windows_scaling():
    """檢測 Windows 縮放比例，如果不是 100% 就彈出教學彈窗並退出程序"""
    try:
        # 獲取系統 DPI
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        
        # 獲取主顯示器的 DPI
        hdc = user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        user32.ReleaseDC(0, hdc)
        
        # 計算縮放比例 (96 DPI = 100%)
        scaling_percentage = int((dpi / 96.0) * 100)
        
        print(f"[系統檢測] 當前 Windows 縮放比例: {scaling_percentage}%")
        
        if scaling_percentage != 100:
            show_scaling_warning_dialog(scaling_percentage)
            return False
        
        return True
        
    except Exception as e:
        print(f"[系統檢測] 檢測縮放比例時出錯: {e}")
        # 如果檢測失敗，假設是 100% 繼續運行
        return True

def show_scaling_warning_dialog(current_scaling):
    """顯示縮放比例警告彈窗和修改教學"""
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    
    dialog = ScalingWarningDialog(current_scaling)
    dialog.exec()
    
    # 確保程序退出
    QApplication.quit()
    sys.exit(0) 