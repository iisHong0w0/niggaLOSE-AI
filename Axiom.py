import win32api
import win32con
import win32gui
import tkinter as tk
import numpy as np
import onnxruntime as ort
import threading
import math
import time 
import cv2
import mss
import ctypes
import queue
import json
from PIL import Image, ImageTk

# Windows 虛擬按鍵碼對應名稱
VK_CODE_MAP = {
    0x01: "滑鼠左鍵",
    0x02: "滑鼠右鍵",
    0x04: "滑鼠中鍵",
    0x05: "滑鼠側鍵1",
    0x06: "滑鼠側鍵2",
    0x08: "Backspace",
    0x09: "Tab",
    0x0D: "Enter",
    0x10: "Shift",
    0x11: "Ctrl",
    0x12: "Alt",
    0x14: "CapsLock",
    0x1B: "Esc",
    0x20: "Space",
    0x25: "←",
    0x26: "↑",
    0x27: "→",
    0x28: "↓",
    0x2C: "PrintScreen",
    0x2D: "Insert",
    0x2E: "Delete",
    0x30: "0",
    0x31: "1",
    0x32: "2",
    0x33: "3",
    0x34: "4",
    0x35: "5",
    0x36: "6",
    0x37: "7",
    0x38: "8",
    0x39: "9",
    0x41: "A",
    0x42: "B",
    0x43: "C",
    0x44: "D",
    0x45: "E",
    0x46: "F",
    0x47: "G",
    0x48: "H",
    0x49: "I",
    0x4A: "J",
    0x4B: "K",
    0x4C: "L",
    0x4D: "M",
    0x4E: "N",
    0x4F: "O",
    0x50: "P",
    0x51: "Q",
    0x52: "R",
    0x53: "S",
    0x54: "T",
    0x55: "U",
    0x56: "V",
    0x57: "W",
    0x58: "X",
    0x59: "Y",
    0x5A: "Z",
    0x5B: "Win",
    0x60: "Num0",
    0x61: "Num1",
    0x62: "Num2",
    0x63: "Num3",
    0x64: "Num4",
    0x65: "Num5",
    0x66: "Num6",
    0x67: "Num7",
    0x68: "Num8",
    0x69: "Num9",
    0x70: "F1",
    0x71: "F2",
    0x72: "F3",
    0x73: "F4",
    0x74: "F5",
    0x75: "F6",
    0x76: "F7",
    0x77: "F8",
    0x78: "F9",
    0x79: "F10",
    0x7A: "F11",
    0x7B: "F12",
    0x90: "NumLock",
    0x91: "ScrollLock",
    0xA0: "Shift(左)",
    0xA1: "Shift(右)",
    0xA2: "Ctrl(左)",
    0xA3: "Ctrl(右)",
    0xA4: "Alt(左)",
    0xA5: "Alt(右)",
    # ...可自行擴充...
}

class Config:
    def __init__(self):
        # 自動獲取螢幕解析度
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        self.width = user32.GetSystemMetrics(0)
        self.height = user32.GetSystemMetrics(1)
        
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        
        # 全螢幕檢測
        self.capture_width = self.width
        self.capture_height = self.height
        self.capture_left = 0
        self.capture_top = 0
        self.crosshairX = self.width // 2
        self.crosshairY = self.height // 2
        self.region = {"top": 0, "left": 0, "width": self.width, "height": self.height}

        self.Running = True
        self.AimToggle = True
        self.InstaStep = False
        self.RectangleB = True
        self.IndividualMovementDelay = None
        self.Sensitivity = 1
        self.delay = 0.000
        self.rectC = None
        self.AimKeys = [0x01, 0x02]  # 預設左鍵(0x01)與右鍵(0x02)
        self.fov_size = 666  # FOV正方形邊長
        self.show_confidence = True  # 顯示概率
        self.min_confidence = 0.66  # 最低概率閾值
        
        # ONNX 模型相關設定
        self.model_input_size = 640
        self.model_path = "rivals.onnx"
        
        # 新增：瞄準部位選擇（head 或 body）
        self.aim_part = "head"  # 預設為頭部

        # 新增：瞄準速度/平滑度 (0.01~1.0)
        self.aim_speed = 0.26  # 預設值

        # 新增：檢測間隔（秒），預設0.01秒（約100FPS）
        self.detect_interval = 0.01
        # 新增：自動開槍鍵（預設滑鼠右鍵）
        self.auto_fire_key = 0x02
        # 新增：自動開槍延遲（秒）
        self.auto_fire_delay = 0.26


config = Config()

# === 新增全螢幕疊加Overlay功能 ===
boxes_overlay = queue.Queue()
confidences_overlay = queue.Queue()  # 新增概率資訊佇列

# --- PyQt6 Overlay ---
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QTimer
import sys

class PyQtOverlay(QWidget):
    def __init__(self, boxes_overlay, confidences_overlay, config):
        super().__init__()
        self.boxes_overlay = boxes_overlay
        self.confidences_overlay = confidences_overlay
        self.config = config
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.screen_width = config.width
        self.screen_height = config.height
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.boxes = []
        self.confidences = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(16)  # 約60FPS
        self.show()

        # 強制滑鼠穿透（Win32 API）
        try:
            import ctypes
            from ctypes import wintypes
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
            self.boxes = self.boxes_overlay.get_nowait()
        except:
            self.boxes = []
        try:
            self.confidences = self.confidences_overlay.get_nowait()
        except:
            self.confidences = []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 畫FOV正方形
        fov = self.config.fov_size
        cx, cy = self.config.crosshairX, self.config.crosshairY
        x1 = cx - fov // 2
        y1 = cy - fov // 2
        x2 = cx + fov // 2
        y2 = cy + fov // 2
        pen = QPen(QColor(255, 0, 0, 180), 2)
        painter.setPen(pen)
        painter.drawRect(x1, y1, fov, fov)
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

# 啟動 PyQt6 Overlay 的 thread

def start_pyqt_overlay():
    app = QApplication(sys.argv)
    overlay = PyQtOverlay(boxes_overlay, confidences_overlay, config)
    app.exec()

def CreateOverlay():
    root = tk.Tk()
    root.title("Axiom_h0pZ")
    root.geometry('1000x555')
    # 主色調
    bg_main = "#250526"
    bg_frame = '#120606'
    fg_text = '#e0e6f0'
    accent = '#230622'
    btn_bg = '#230622'
    btn_active = '#230622'
    scale_trough = '#230622'
    scale_slider = '#230622'

    # 設定小圖標（強制轉ico）
    import os
    icon_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    try:
        from PIL import Image
        tmp_ico = os.path.join(os.path.dirname(__file__), '_tmp_logo.ico')
        img = Image.open(icon_path)
        img.save(tmp_ico, format='ICO', sizes=[(32,32)])
        root.iconbitmap(tmp_ico)
    except Exception as e:
        pass  # 若失敗則不顯示icon

    root.configure(bg=bg_main)
    # 加入logo圖片
    try:
        from PIL import ImageTk
        logo_img = Image.open(icon_path)
        logo_img = logo_img.resize((48, 48))
        logo_tk = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo_tk, bg=bg_main)
        logo_label.image = logo_tk  # 防止被GC
        logo_label.pack(side="top", pady=(8, 0))
    except:
        pass
    tk.Label(root, text="Axiom V3", font=("Helvetica", 14, "bold"), bg=bg_main, fg=fg_text).pack(side="top")

    main_canvas = tk.Canvas(root, height=400, bg=bg_main, highlightthickness=0)
    main_canvas.pack(side="top", fill="both", expand=True)
    h_scroll = tk.Scrollbar(root, orient="horizontal", command=main_canvas.xview)
    h_scroll.pack(side="bottom", fill="x")
    main_canvas.configure(xscrollcommand=h_scroll.set)
    content_frame = tk.Frame(main_canvas, bg=bg_main)
    main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def on_configure(event):
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    content_frame.bind("<Configure>", on_configure)

    # LabelFrame 樣式
    def style_labelframe(frame, text):
        lf = tk.LabelFrame(frame, text=text, font=("Arial", 11, "bold"), labelanchor="n",
                          bg=bg_frame, fg=fg_text, bd=2, relief="groove", highlightbackground=accent)
        lf.configure(highlightcolor=accent)
        return lf

    left_frame = style_labelframe(content_frame, "基本控制區")
    middle_frame = style_labelframe(content_frame, "參數調整區")
    right_frame = style_labelframe(content_frame, "顯示/按鍵區")
    left_frame.pack(side="left", fill="y", padx=10, pady=10)
    middle_frame.pack(side="left", fill="y", padx=10, pady=10)
    right_frame.pack(side="left", fill="y", padx=10, pady=10)

    def quitProgram():
        config.AimToggle = False
        config.Running = False
        save_config()
        root.quit()

    def SensitivityConfigurator(Sens):
        config.Sensitivity = float(Sens)

    def ManualCenterConfiguratorX(ValueX):
        config.crosshairX = config.width // 2 + int(ValueX)
        config.center_x = config.width // 2 + int(ValueX)

    def ManualCenterConfiguratorY(ValueY):
        config.crosshairY = config.height // 2 + int(ValueY)
        config.center_y = config.height // 2 + int(ValueY)

    def CoefficientXConfigurator(ValueX):
        config.MovementCoefficientX = float(ValueX)

    def CoefficientYConfigurator(ValueY):
        config.MovementCoefficientY = float(ValueY)

    def InstaStepButton():
        pass  # 已無效，直接 pass

    def AimButton():
        config.AimToggle = not config.AimToggle
        AimLabel.config(text=f"自動瞄準目前狀態: {config.AimToggle}")

    def ShowHideRect():
        config.RectangleB = not config.RectangleB

    def CreateSlider(frame, LabelText, fromV, toV, resolution, command, setValue):
        group = tk.Frame(frame, bg=bg_frame)
        group.pack(side="left", padx=5, pady=5)
        tk.Label(group, text=LabelText, bg=bg_frame, fg=fg_text).pack()
        Slider = tk.Scale(group, from_=fromV, to=toV, resolution=resolution, orient=tk.VERTICAL, length=260, command=command,
                          bg=bg_frame, fg=fg_text, troughcolor=scale_trough, highlightbackground=accent, activebackground=scale_slider)
        Slider.pack()
        Slider.set(setValue)

    # FOV大小調整
    def FovSizeConfigurator(val):
        config.fov_size = int(val)

    # 最低概率調整（改為0~100%）
    def MinConfidenceConfigurator(val):
        config.min_confidence = float(val) / 100.0

    # 顯示概率切換
    def ToggleShowConfidence():
        config.show_confidence = not config.show_confidence
        ConfidenceLabel.config(text=f"顯示概率: {config.show_confidence}")

    # ===== 左側區塊：基本控制 =====
    AimLabel = tk.Label(left_frame, text=f"自動瞄準目前狀態: {config.AimToggle}", bg=bg_frame, fg=fg_text)
    AimLabel.pack(pady=2)
    # 新增：顯示執行提供者狀態
    provider_text = {
        "DmlExecutionProvider": "DirectML (GPU)",
        "CPUExecutionProvider": "CPU",
    }
    provider_str = provider_text.get(getattr(config, 'current_provider', ''), getattr(config, 'current_provider', '未知'))
    ProviderLabel = tk.Label(left_frame, text=f"推論加速: {provider_str}", bg=bg_frame, fg=fg_text)
    ProviderLabel.pack(pady=2)
    AimToggler = tk.Button(left_frame, text="切換自動瞄準", command=AimButton, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    AimToggler.pack(pady=2)
    QuitButton = tk.Button(left_frame, text="退出並保存參數", command=quitProgram, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    QuitButton.pack(pady=10)

    # ===== 中間區塊：參數調整（橫向分組） =====
    CreateSlider(middle_frame, "fov左右座標", -100, 100, 1, ManualCenterConfiguratorX, 0)
    CreateSlider(middle_frame, "fov上下座標", -100, 100, 1, ManualCenterConfiguratorY, 0)
    # CreateSlider(middle_frame, "遊戲靈敏度", 0.1, 10, 0.01, SensitivityConfigurator, config.Sensitivity) # 如需開啟請取消註解
    CreateSlider(middle_frame, "FOV大小", 50, min(config.width, config.height), 1, FovSizeConfigurator, config.fov_size)
    CreateSlider(middle_frame, "概率閾值(%)", 0, 100, 1, MinConfidenceConfigurator, int(config.min_confidence * 100))
    # CreateSlider(middle_frame, "自動瞄準速度", 1, 26, 1, PixelPerStepConfigurator, config.PixelPerStep)
    def AimSpeedConfigurator(val):
        config.aim_speed = float(val) / 100.0
    CreateSlider(middle_frame, "自動瞄準速度", 0, 200, 1, AimSpeedConfigurator, int(config.aim_speed * 100))
    # 新增：檢測間隔滑桿（1~100 ms）
    def DetectIntervalConfigurator(val):
        # 將滑桿值(毫秒)轉為秒
        config.detect_interval = int(val) / 1000.0
    CreateSlider(middle_frame, "檢測間隔(ms)", 0, 100, 1, DetectIntervalConfigurator, int(config.detect_interval * 1000))

    # ===== 右側區塊：顯示選項與按鍵 =====
    ConfidenceLabel = tk.Label(right_frame, text=f"顯示概率: {config.show_confidence}", bg=bg_frame, fg=fg_text)
    ConfidenceLabel.pack(pady=2)
    ToggleConfidenceButton = tk.Button(right_frame, text="切換顯示概率", command=ToggleShowConfidence, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    ToggleConfidenceButton.pack(pady=2)

    # ===== 開鏡延遲滑桿 =====
    def AutoFireDelayConfigurator(val):
        config.auto_fire_delay = float(val)
        AutoFireDelayLabel.config(text=f"開鏡延遲: {float(val):.2f} 秒")
    AutoFireDelayLabel = tk.Label(right_frame, text=f"開鏡延遲: {config.auto_fire_delay:.2f} 秒", bg=bg_frame, fg=fg_text)
    AutoFireDelayLabel.pack(pady=(10,0))
    AutoFireDelaySlider = tk.Scale(right_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, length=160,
                                   command=AutoFireDelayConfigurator, bg=bg_frame, fg=fg_text, troughcolor=scale_trough,
                                   highlightbackground=accent, activebackground=scale_slider)
    AutoFireDelaySlider.set(config.auto_fire_delay)
    AutoFireDelaySlider.pack(pady=(0,8))

    # ===== 新版「啟用瞄準按鍵」功能 =====
    tk.Label(right_frame, text="啟用瞄準按鍵：", bg=bg_frame, fg=fg_text).pack()
    tk.Label(right_frame, text="（點擊下方按鈕可更改綁定，支援滑鼠與鍵盤）", bg=bg_frame, fg="#b0b0b0", font=("Arial", 9)).pack(pady=(0, 6))
    listening_for_slot = {'slot': None}  # slot: 1=瞄準1, 2=瞄準2, 3=自動開槍
    aimkey_btns = [None, None]
    autofire_btn = None

    def get_key_name(key_code):
        if key_code is None:
            return '[點擊以設定]'
        return VK_CODE_MAP.get(key_code, f'0x{key_code:02X}')

    def update_aimkey_btn(slot):
        if slot == 0 or slot == 1:
            key_code = config.AimKeys[slot] if slot < len(config.AimKeys) else None
            aimkey_btns[slot]['text'] = get_key_name(key_code)
        elif slot == 2:
            autofire_btn['text'] = get_key_name(config.auto_fire_key)

    def set_listen(slot):
        def inner():
            listening_for_slot['slot'] = slot + 1
            if slot == 0 or slot == 1:
                aimkey_btns[slot]['text'] = '[請按下任意按鍵...]'
            elif slot == 2:
                autofire_btn['text'] = '[請按下任意按鍵...]'
        return inner

    for i in range(2):
        tk.Label(right_frame, text=f"按鍵 {i+1}:", bg=bg_frame, fg=fg_text).pack()
        btn = tk.Button(right_frame, text=get_key_name(config.AimKeys[i] if i < len(config.AimKeys) else None),
                        width=16, command=set_listen(i), bg=btn_bg, fg=fg_text, activebackground=btn_active)
        btn.pack(side='top', pady=2)
        aimkey_btns[i] = btn
    # 自動開槍鍵
    tk.Label(right_frame, text="自動開槍鍵：", bg=bg_frame, fg=fg_text).pack(pady=(10,0))
    autofire_btn = tk.Button(right_frame, text=get_key_name(getattr(config, 'auto_fire_key', 0x02)),
                            width=16, command=set_listen(2), bg=btn_bg, fg=fg_text, activebackground=btn_active)
    autofire_btn.pack(side='top', pady=2)

    def key_listener():
        slot = listening_for_slot['slot']
        if slot is not None:
            mouse_keys = [0x01, 0x02, 0x04, 0x05, 0x06]
            detected = False
            for key_code in mouse_keys:
                if win32api.GetAsyncKeyState(key_code) & 0x8000:
                    if slot == 1 or slot == 2:
                        config.AimKeys[slot-1] = key_code
                    elif slot == 3:
                        config.auto_fire_key = key_code
                    update_aimkey_btn(slot-1)
                    listening_for_slot['slot'] = None
                    detected = True
                    break
            if not detected:
                for key_code in range(8, 256):
                    if win32api.GetAsyncKeyState(key_code) & 0x8000:
                        if slot == 1 or slot == 2:
                            config.AimKeys[slot-1] = key_code
                        elif slot == 3:
                            config.auto_fire_key = key_code
                        update_aimkey_btn(slot-1)
                        listening_for_slot['slot'] = None
                        break
        root.after(20, key_listener)
    key_listener()

    # 瞄準部位
    def AimPartChanged(event=None):
        config.aim_part = AimPartVar.get()
    AimPartVar = tk.StringVar(value=config.aim_part)
    tk.Label(right_frame, text="瞄準部位：", bg=bg_frame, fg=fg_text).pack()
    AimPartMenu = tk.OptionMenu(right_frame, AimPartVar, "head", "body", command=AimPartChanged)
    AimPartMenu.config(bg=btn_bg, fg=fg_text, activebackground=btn_active, highlightbackground=accent)
    AimPartMenu.pack()

    root.mainloop()

def is_target_in_fov(target_x, target_y):
    """檢查目標是否在FOV範圍內"""
    fov_half = config.fov_size // 2
    dx = abs(target_x - config.crosshairX)
    dy = abs(target_y - config.crosshairY)
    return dx <= fov_half and dy <= fov_half

def preprocess_image(image):
    """預處理圖像以適配ONNX模型"""
    # 調整大小到640x640
    resized = cv2.resize(image, (config.model_input_size, config.model_input_size))
    
    # 轉換為RGB格式
    rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    
    # 正規化到0-1範圍並轉換為float32
    normalized = rgb_image.astype(np.float32) / 255.0
    
    # 轉換維度順序為NCHW (batch, channels, height, width)
    input_tensor = np.transpose(normalized, (2, 0, 1))
    input_tensor = np.expand_dims(input_tensor, axis=0)
    
    return input_tensor

def postprocess_outputs(outputs, original_width, original_height):
    """後處理ONNX模型輸出"""
    # 獲取輸出 (通常是 [batch, 84, 8400] 格式)
    predictions = outputs[0][0]  # 移除batch維度
    
    # 轉置為 [8400, 84]
    predictions = predictions.T
    
    # 提取座標和置信度
    boxes = []
    confidences = []
    
    # 計算縮放比例
    scale_x = original_width / config.model_input_size
    scale_y = original_height / config.model_input_size
    
    for detection in predictions:
        # 前4個值是座標 (cx, cy, w, h)
        cx, cy, w, h = detection[:4]
        
        # 第5個值是置信度 (因為只有一個類別)
        confidence = detection[4]
        
        if confidence >= config.min_confidence:
            # 轉換為xyxy格式並縮放回原始大小
            x1 = (cx - w / 2) * scale_x
            y1 = (cy - h / 2) * scale_y
            x2 = (cx + w / 2) * scale_x
            y2 = (cy + h / 2) * scale_y
            
            boxes.append([x1, y1, x2, y2])
            confidences.append(confidence)
    
    return boxes, confidences

def non_max_suppression(boxes, confidences, iou_threshold=0.4):
    """非極大值抑制"""
    if len(boxes) == 0:
        return [], []
    
    # 轉換為numpy陣列
    boxes = np.array(boxes)
    confidences = np.array(confidences)
    
    # 計算面積
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    
    # 根據置信度排序
    order = confidences.argsort()[::-1]
    
    keep = []
    while len(order) > 0:
        # 選擇置信度最高的框
        i = order[0]
        keep.append(i)
        
        if len(order) == 1:
            break
        
        # 計算IoU
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        
        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        intersection = w * h
        
        union = areas[i] + areas[order[1:]] - intersection
        iou = intersection / union
        
        # 保留IoU小於閾值的框
        order = order[1:][iou <= iou_threshold]
    
    return boxes[keep].tolist(), confidences[keep].tolist()

# 滑鼠移動（SendInput）
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUT_UNION)]

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001


def send_mouse_move(dx, dy):
    extra = ctypes.c_ulong(0)
    ii_ = INPUT._INPUT_UNION()
    ii_.mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    command = INPUT(INPUT_MOUSE, ii_)
    ctypes.windll.user32.SendInput(1, ctypes.byref(command), ctypes.sizeof(command))


def save_config():
    data = {
        'fov_size': config.fov_size,
        'aim_speed': config.aim_speed,
        'aim_part': config.aim_part,
        'AimKeys': config.AimKeys,
        'auto_fire_key': getattr(config, 'auto_fire_key', 0x02),
        'auto_fire_delay': getattr(config, 'auto_fire_delay', 1.0),
        'min_confidence': config.min_confidence,
        'show_confidence': config.show_confidence,
        'crosshairX': config.crosshairX,
        'crosshairY': config.crosshairY,
        'Sensitivity': config.Sensitivity,
        'detect_interval': config.detect_interval,
    }
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"設定儲存失敗: {e}")

def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in data.items():
            setattr(config, k, v)
        print("設定檔已載入")
    except FileNotFoundError:
        print("未找到設定檔，使用預設值")
    except Exception as e:
        print(f"設定載入失敗: {e}")

def main():
    try:
        # 嘗試使用 DirectML (DML) GPU 加速，失敗則自動退回 CPU
        providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
        print(f"正在載入模型: {config.model_path}")
        session = ort.InferenceSession(config.model_path, providers=providers)
        input_name = session.get_inputs()[0].name
        print(f"模型載入成功！輸入名稱: {input_name}")
        print(f"模型輸入形狀: {session.get_inputs()[0].shape}")
        print(f"模型輸出形狀: {session.get_outputs()[0].shape}")
        provider = session.get_providers()[0]
        print(f"實際使用的執行提供者: {provider}")
        config.current_provider = provider
    except Exception as e:
        print(f"載入模型失敗: {e}")
        return
    
    # 嘗試載入設定檔
    load_config()
    
    indexMin = 0
    x1=y1=x2=y2=0
    screenCapture = mss.mss()
    overlayThread = threading.Thread(target=CreateOverlay)
    overlayThread.start()

    # ====== 自動開槍功能（含開鏡延遲） ======
    def auto_fire_loop():
        import time
        last_key_state = 0
        delay_start_time = None
        delay_done = False
        while config.Running:
            key_code = getattr(config, 'auto_fire_key', 0x02)
            key_state = win32api.GetAsyncKeyState(key_code) & 0x8000
            if key_state and not last_key_state:
                # 按下自動開槍鍵，開始延遲計時
                delay_start_time = time.time()
                delay_done = False
            if key_state:
                if delay_start_time is not None and not delay_done:
                    # 尚在延遲期間
                    if time.time() - delay_start_time >= getattr(config, 'auto_fire_delay', 1.0):
                        delay_done = True
                if delay_done:
                    # 取得中心點座標
                    cx, cy = config.crosshairX, config.crosshairY
                    # 取得目前所有敵人框（絕對座標）
                    try:
                        boxes = list(boxes_overlay.queue[-1]) if boxes_overlay.qsize() > 0 else []
                    except Exception:
                        boxes = []
                    # 檢查中心點是否在任一框內
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box)
                        if x1 <= cx <= x2 and y1 <= cy <= y2:
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                            time.sleep(0.01)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                            break
            else:
                # 鍵已鬆開，重置狀態
                delay_start_time = None
                delay_done = False
            last_key_state = key_state
            time.sleep(0.006)
    auto_fire_thread = threading.Thread(target=auto_fire_loop, daemon=True)
    auto_fire_thread.start()
    
    while config.Running:
        # 如果沒有按下瞄準鍵，就暫停一下，避免空轉浪費CPU
        if not config.AimToggle or not any(win32api.GetAsyncKeyState(k) & 0x8000 for k in config.AimKeys):
            time.sleep(config.detect_interval)
            continue

        # 1. 動態更新擷取區域 (FOV)
        fov_size = config.fov_size
        config.region['left'] = config.crosshairX - fov_size // 2
        config.region['top'] = config.crosshairY - fov_size // 2
        config.region['width'] = fov_size
        config.region['height'] = fov_size

        # 2. 擷取螢幕 (只抓FOV區域)
        GameFrame = np.array(screenCapture.grab(config.region))
        if GameFrame.size == 0:
            continue
        GameFrame = cv2.cvtColor(GameFrame, cv2.COLOR_BGRA2BGR)

        # 3. 執行推理
        input_tensor = preprocess_image(GameFrame)
        try:
            outputs = session.run(None, {input_name: input_tensor})
            boxes, confidences = postprocess_outputs(outputs, fov_size, fov_size)
            boxes, confidences = non_max_suppression(boxes, confidences)
        except Exception as e:
            print(f"推理錯誤: {e}")
            continue

        valid_targets = []
        absolute_boxes = []
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i]
            abs_x1 = config.region['left'] + x1
            abs_y1 = config.region['top'] + y1
            abs_x2 = config.region['left'] + x2
            abs_y2 = config.region['top'] + y2
            absolute_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])
            target_x = (abs_x2 + abs_x1) / 2
            if config.aim_part == "head":
                target_y = abs_y1 + (abs_y2 - abs_y1) * 0.085
            else:
                target_y = (abs_y1 + abs_y2) / 2
            if is_target_in_fov(target_x, target_y):
                moveX = target_x - config.crosshairX
                moveY = target_y - config.crosshairY
                distance = math.sqrt(moveX**2 + moveY**2)
                valid_targets.append((distance, moveX, moveY))
        if valid_targets:
            valid_targets.sort(key=lambda x: x[0])
            _, moveX, moveY = valid_targets[0]
            dx = int(moveX * config.aim_speed)
            dy = int(moveY * config.aim_speed)
            if abs(dx) > 0 or abs(dy) > 0:
                send_mouse_move(dx, dy)
        try:
            boxes_overlay.queue.clear()
            confidences_overlay.queue.clear()
        except:
            pass
        boxes_overlay.put(absolute_boxes)
        confidences_overlay.put(confidences)
    cv2.destroyAllWindows()
    overlayThread.join()
                 
if __name__ == "__main__":
    load_config()
    # 先啟動 AI 主循環於子執行緒
    ai_thread = threading.Thread(target=main, daemon=True)
    ai_thread.start()
    # 主執行緒跑 PyQt6 overlay
    start_pyqt_overlay()