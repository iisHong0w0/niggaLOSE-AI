# status_panel.py
import os
import sys
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer
import ctypes
from ctypes import wintypes
from language_manager import get_text, language_manager  # <-- 修改: 導入 get_text 和 language_manager

# --- 顏色設定 ---
TEXT_COLOR = QColor("#FFFFFF")
AIM_ON_COLOR = QColor("#00AC09")
AIM_OFF_COLOR = QColor("#AF0000")

def draw_text_with_outline(painter, x, y, text, text_color, outline_color=QColor(0,0,0), outline_width=1):
    """在指定位置繪製帶有邊框的文字"""
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            if dx != 0 or dy != 0:
                painter.setPen(outline_color)
                painter.drawText(x+dx, y+dy, text)
    painter.setPen(text_color)
    painter.drawText(x, y, text)

class StatusPanel(QWidget):
    """
    一個獨立的 PyQt6 視窗，用於在螢幕左上角顯示 Axiom 的 Logo 和運行狀態。
    這個視窗會保持在最上層，且滑鼠事件會穿透它，不會影響遊戲操作。
    """
    def __init__(self, config):
        super().__init__()
        self.config = config

        # --- 視窗基本設定 ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |    # 無邊框
            Qt.WindowType.WindowStaysOnTopHint |   # 總在最前
            Qt.WindowType.Tool |                   # 不在任務欄顯示
            Qt.WindowType.WindowTransparentForInput  # 關鍵：透明輸入
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # --- 設定視窗位置與大小 (可根據需求調整) ---
        self.setGeometry(10, 10, 350, 150)
        
        # --- 載入 Logo ---
        logo_path = 'logo.png'
        if os.path.exists(logo_path):
            self.logo = QPixmap(logo_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            self.logo = None
            print("狀態面板警告: 在目錄中找不到 logo.png")

        # --- 定時更新 ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        # 優化：狀態面板更新頻率較低即可，因為狀態變化不頻繁
        self.timer.start(500)  # 降低到500ms，減少不必要的重繪
        
        # 優化：緩存上一次的狀態，避免不必要的重繪
        self.last_aim_state = None
        self.last_provider = None
        self.last_model_path = None
        self.last_language = language_manager.get_current_language()  # 追蹤語言變化

    def showEvent(self, event):
        """視窗顯示時設定滑鼠穿透"""
        super().showEvent(event)
        if sys.platform == "win32":
            # 延遲一下確保視窗完全初始化
            QTimer.singleShot(100, self.set_click_through)

    def set_click_through(self):
        """使用 Win32 API 設定視窗的滑鼠穿透屬性"""
        if sys.platform != "win32":
            return
            
        try:
            # 獲取視窗句柄 (HWND)
            hwnd = int(self.winId())
            
            # 定義 Win32 API 常數
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            
            # 獲取 user32.dll
            user32 = ctypes.windll.user32
            
            # 獲取當前擴展樣式
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # 設定新的擴展樣式
            new_ex_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex_style)
            
            print("狀態面板: 已成功設定滑鼠穿透。")
            return True

        except Exception as e:
            print(f"狀態面板錯誤: 設定滑鼠穿透失敗 - {e}")
            return False

    def update_display(self):
        """觸發重繪事件 - 優化版本，只在狀態改變時重繪"""
        # 檢查狀態是否有變化
        current_aim_state = self.config.AimToggle
        current_provider = getattr(self.config, 'current_provider', 'CPUExecutionProvider')
        current_model_path = getattr(self.config, 'model_path', '')
        current_language = language_manager.get_current_language()  # 檢查語言變化
        
        # 只有狀態發生變化時才觸發重繪
        if (current_aim_state != self.last_aim_state or 
            current_provider != self.last_provider or 
            current_model_path != self.last_model_path or
            current_language != self.last_language):  # 新增語言變化檢查
            
            self.last_aim_state = current_aim_state
            self.last_provider = current_provider
            self.last_model_path = current_model_path
            self.last_language = current_language  # 更新語言狀態
            self.update()  # 觸發重繪

    def paintEvent(self, event):
        """
        繪製事件，所有繪圖邏輯都在此處。
        """
        if not getattr(self.config, 'show_status_panel', False):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        axiom_font = QFont('Arial', 24, QFont.Weight.Bold)
        status_font = QFont('Arial', 10, QFont.Weight.Bold)
        text_color = TEXT_COLOR
        
        x_offset, y_offset = 10, 10

        if self.logo:
            painter.drawPixmap(x_offset, y_offset, self.logo)
            x_offset += self.logo.width() + 10

        painter.setFont(axiom_font)
        draw_text_with_outline(painter, x_offset, y_offset + 35, "Axiom", text_color)
        
        y_offset += 60
        x_offset = 10
        painter.setFont(status_font)
        
        # --- 修改開始: 使用 get_text 實現國際化 ---
        is_aim_on = self.config.AimToggle
        aim_status_text = get_text("status_panel_on") if is_aim_on else get_text("status_panel_off")
        aim_color = AIM_ON_COLOR if is_aim_on else AIM_OFF_COLOR
        draw_text_with_outline(painter, x_offset, y_offset, f"{get_text('auto_aim')}: {aim_status_text}", aim_color)
        y_offset += 20
        
        provider_text = get_text("gpu_directml") if "Dml" in self.config.current_provider else get_text("cpu")
        draw_text_with_outline(painter, x_offset, y_offset, f"{get_text('status_panel_compute_mode')}: {provider_text}", text_color)
        y_offset += 20
        
        model_name = os.path.basename(self.config.model_path)
        draw_text_with_outline(painter, x_offset, y_offset, f"{get_text('status_panel_current_model')}: {model_name}", text_color)