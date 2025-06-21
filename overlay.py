# overlay.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QTimer
import ctypes
from ctypes import wintypes

class PyQtOverlay(QWidget):
    def __init__(self, boxes_queue, confidences_queue, config):
        super().__init__()
        self.boxes_queue = boxes_queue
        self.confidences_queue = confidences_queue
        self.config = config
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.setGeometry(0, 0, config.width, config.height)
        self.boxes = []
        self.confidences = []
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(16)  # ~60 FPS
        self.show()
        self.set_click_through()

    def set_click_through(self):
        try:
            hwnd = self.winId().__int__()
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception as e:
            print(f"滑鼠穿透設置失敗: {e}")

    def update_overlay(self):
        try:
            self.boxes = self.boxes_queue.get_nowait()
            self.confidences = self.confidences_queue.get_nowait()
        except:
            # Keep last known boxes if queue is empty
            pass
        self.update()

    def paintEvent(self, event):
        if not self.config.AimToggle: # 如果關閉了功能，就不繪製
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 畫FOV
        fov = self.config.fov_size
        cx, cy = self.config.crosshairX, self.config.crosshairY
        pen = QPen(QColor(255, 0, 0, 180), 2)
        painter.setPen(pen)
        painter.drawRect(cx - fov // 2, cy - fov // 2, fov, fov)

        # 畫人物框與概率
        pen_box = QPen(QColor(0, 255, 0, 200), 3)
        painter.setPen(pen_box)
        font = QFont('Arial', 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        for i, box in enumerate(self.boxes):
            x1, y1, x2, y2 = map(int, box)
            painter.drawRect(x1, y1, x2-x1, y2-y1)
            if self.config.show_confidence and i < len(self.confidences):
                confidence = self.confidences[i]
                text = f"{confidence:.0%}"
                painter.setPen(QPen(QColor(255, 255, 0, 220), 2))
                painter.drawText(x1, y1-8, text)
                painter.setPen(pen_box)

def start_pyqt_overlay(boxes_queue, confidences_queue, config):
    app = QApplication(sys.argv)
    overlay = PyQtOverlay(boxes_queue, confidences_queue, config)
    sys.exit(app.exec())