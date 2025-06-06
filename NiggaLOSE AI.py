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
from PIL import Image, ImageTk


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
        self.MovementCoefficientX = 0.15
        self.MovementCoefficientY = 0.15
        self.movementSteps = 20
        self.delay = 0.001
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


config = Config()

# === 新增全螢幕疊加Overlay功能 ===
boxes_overlay = queue.Queue()
confidences_overlay = queue.Queue()  # 新增概率資訊佇列

def CreateOverlay():
    root = tk.Tk()
    root.title("NiggaLOSE AI_h0pZ")
    root.geometry('999x333')
    # 主色調
    bg_main = '#1a233a'  # 深藍
    bg_frame = '#223366'  # 淡藍
    fg_text = '#e0e6f0'  # 亮文字
    accent = '#3a7bd5'   # 藍色強調
    btn_bg = '#2a3d5c'
    btn_active = '#3a7bd5'
    scale_trough = '#2a3d5c'
    scale_slider = '#5fa8e6'

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
    tk.Label(root, text="NiggaLOSE AI V2", font=("Helvetica", 14, "bold"), bg=bg_main, fg=fg_text).pack(side="top")

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
        root.quit()

    def SensitivityConfigurator(Sens):
        config.Sensitivity = float(Sens)

    def DelayConfigurator(Delay):
        config.delay = max(0.001, float(Delay))

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
        config.InstaStep = not config.InstaStep
        if config.InstaStep == True:
            InstaStepLabel.config(text=f"每次移動目前分為 1 步")
            config.movementSteps = 1
        else:
            config.movementSteps = 5
            InstaStepLabel.config(text=f"每次移動目前分為 {config.movementSteps} 步")

    def AimButton():
        config.AimToggle = not config.AimToggle
        AimLabel.config(text=f"自動瞄準目前狀態: {config.AimToggle}")

    def ShowHideRect():
        config.RectangleB = not config.RectangleB

    def CreateSlider(frame, LabelText, fromV, toV, resolution, command, setValue):
        group = tk.Frame(frame, bg=bg_frame)
        group.pack(side="left", padx=5, pady=5)
        tk.Label(group, text=LabelText, bg=bg_frame, fg=fg_text).pack()
        Slider = tk.Scale(group, from_=fromV, to=toV, resolution=resolution, orient=tk.VERTICAL, command=command, length=120,
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
    AimToggler = tk.Button(left_frame, text="切換自動瞄準", command=AimButton, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    AimToggler.pack(pady=2)
    InstaStepLabel = tk.Label(left_frame, text=f"每次移動目前分為 {config.movementSteps} 步", bg=bg_frame, fg=fg_text)
    InstaStepLabel.pack(pady=2)
    InstaStepBtn = tk.Button(left_frame, text="切換步數(瞬移)", command=InstaStepButton, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    InstaStepBtn.pack(pady=2)
    QuitButton = tk.Button(left_frame, text="退出", command=quitProgram, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    QuitButton.pack(pady=10)

    # ===== 中間區塊：參數調整（橫向分組） =====
    CreateSlider(middle_frame, "fov左右座標", -100, 100, 1, ManualCenterConfiguratorX, 0)
    CreateSlider(middle_frame, "fov上下座標", -100, 100, 1, ManualCenterConfiguratorY, 0)
    # CreateSlider(middle_frame, "遊戲靈敏度", 0.1, 10, 0.01, SensitivityConfigurator, config.Sensitivity) # 如需開啟請取消註解
    CreateSlider(middle_frame, "移動間隔", 0.001, 0.05, 0.001, DelayConfigurator, config.delay)
    CreateSlider(middle_frame, "移動速度水平", 0, 5, 0.01, CoefficientXConfigurator, config.MovementCoefficientX)
    CreateSlider(middle_frame, "移動速度上下", 0, 5, 0.01, CoefficientYConfigurator, config.MovementCoefficientY)
    CreateSlider(middle_frame, "FOV大小", 50, min(config.width, config.height), 1, FovSizeConfigurator, config.fov_size)
    CreateSlider(middle_frame, "概率閾值(%)", 0, 100, 1, MinConfidenceConfigurator, int(config.min_confidence * 100))
    def MovementStepsConfigurator(val):
        config.movementSteps = int(val)
        InstaStepLabel.config(text=f"每次移動目前分為 {config.movementSteps} 步")
    CreateSlider(middle_frame, "移動步數", 1, 20, 1, MovementStepsConfigurator, config.movementSteps)

    # ===== 右側區塊：顯示選項與按鍵 =====
    ConfidenceLabel = tk.Label(right_frame, text=f"顯示概率: {config.show_confidence}", bg=bg_frame, fg=fg_text)
    ConfidenceLabel.pack(pady=2)
    ToggleConfidenceButton = tk.Button(right_frame, text="切換顯示概率", command=ToggleShowConfidence, bg=btn_bg, fg=fg_text, activebackground=btn_active)
    ToggleConfidenceButton.pack(pady=2)
    # 瞄準按鍵
    AimKeyVar1 = tk.BooleanVar(value=0x01 in config.AimKeys)
    AimKeyVar2 = tk.BooleanVar(value=0x02 in config.AimKeys)
    def updateAimKeys(*args):
        keys = []
        if AimKeyVar1.get():
            keys.append(0x01)
        if AimKeyVar2.get():
            keys.append(0x02)
        config.AimKeys = keys
    AimKeyVar1.trace_add('write', updateAimKeys)
    AimKeyVar2.trace_add('write', updateAimKeys)
    tk.Label(right_frame, text="啟用瞄準按鍵：", bg=bg_frame, fg=fg_text).pack()
    cb1 = tk.Checkbutton(right_frame, text="左鍵", variable=AimKeyVar1, bg=bg_frame, fg=fg_text, activebackground=btn_active, selectcolor=accent)
    cb1.pack()
    cb2 = tk.Checkbutton(right_frame, text="右鍵", variable=AimKeyVar2, bg=bg_frame, fg=fg_text, activebackground=btn_active, selectcolor=accent)
    cb2.pack()
    updateAimKeys()
    # 瞄準部位
    def AimPartChanged(event=None):
        config.aim_part = AimPartVar.get()
    AimPartVar = tk.StringVar(value=config.aim_part)
    tk.Label(right_frame, text="瞄準部位：", bg=bg_frame, fg=fg_text).pack()
    AimPartMenu = tk.OptionMenu(right_frame, AimPartVar, "head", "body", command=AimPartChanged)
    AimPartMenu.config(bg=btn_bg, fg=fg_text, activebackground=btn_active, highlightbackground=accent)
    AimPartMenu.pack()

    root.mainloop()

def overlay_drawer():
    import tkinter as tk
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.attributes('-transparentcolor', 'white')
    root.overrideredirect(True)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg='white', highlightthickness=0)
    canvas.pack()

    def redraw():
        canvas.delete('all')
        # 畫FOV正方形
        fov = config.fov_size
        cx, cy = config.crosshairX, config.crosshairY
        x1 = cx - fov // 2
        y1 = cy - fov // 2
        x2 = cx + fov // 2
        y2 = cy + fov // 2
        canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
        
        # 獲取檢測框和概率
        try:
            boxes = boxes_overlay.get_nowait()
            confidences = confidences_overlay.get_nowait()
        except:
            boxes = []
            confidences = []
            
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            abs_x1 = x1 + config.capture_left
            abs_y1 = y1 + config.capture_top
            abs_x2 = x2 + config.capture_left
            abs_y2 = y2 + config.capture_top
            
            # 繪製檢測框
            canvas.create_rectangle(abs_x1, abs_y1, abs_x2, abs_y2, outline='green', width=3)
            
            # 顯示概率（如果啟用）
            if config.show_confidence and i < len(confidences):
                confidence = confidences[i]
                text = f"{confidence:.0%}"
                # 在框的左上角顯示概率
                canvas.create_text(abs_x1, abs_y1-10, text=text, fill='yellow', 
                                 font=('Arial', 12, 'bold'), anchor='sw')
        
        root.after(16, redraw)

    redraw()
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

def main():
    try:
        # 載入ONNX模型
        print(f"正在載入模型: {config.model_path}")
        session = ort.InferenceSession(config.model_path)
        input_name = session.get_inputs()[0].name
        print(f"模型載入成功！輸入名稱: {input_name}")
        print(f"模型輸入形狀: {session.get_inputs()[0].shape}")
        print(f"模型輸出形狀: {session.get_outputs()[0].shape}")
    except Exception as e:
        print(f"載入模型失敗: {e}")
        return
    
    indexMin = 0
    x1=y1=x2=y2=0
    screenCapture = mss.mss()
    overlayThread = threading.Thread(target=CreateOverlay)
    overlayThread.start()
    overlayBoxThread = threading.Thread(target=overlay_drawer, daemon=True)
    overlayBoxThread.start()
    
    while config.Running:
        time.sleep(0.001)
        if config.AimToggle == False or not any(win32api.GetAsyncKeyState(k) & 0x8000 for k in config.AimKeys):
            time.sleep(0.01)
            continue
            
        # 擷取螢幕
        GameFrame = np.array(screenCapture.grab(config.region))
        GameFrame = cv2.cvtColor(GameFrame, cv2.COLOR_BGRA2BGR)
        
        # 預處理圖像
        input_tensor = preprocess_image(GameFrame)
        
        # 執行推理
        try:
            outputs = session.run(None, {input_name: input_tensor})
            boxes, confidences = postprocess_outputs(outputs, GameFrame.shape[1], GameFrame.shape[0])
            
            # 應用非極大值抑制
            boxes, confidences = non_max_suppression(boxes, confidences)
            
        except Exception as e:
            print(f"推理錯誤: {e}")
            continue
        
        # 找出FOV範圍內最近的目標
        valid_targets = []
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i]
            target_x = (x2 + x1) // 2  # 目標中心X
            # 根據 config.aim_part 決定瞄準點
            if config.aim_part == "head":
                target_y = y1 + (y2 - y1) * 0.085  # 頭部
            else:
                target_y = (y1 + y2) // 2  # 身體（正中心）
            # 檢查是否在FOV範圍內
            if is_target_in_fov(target_x, target_y):
                moveX = target_x - config.crosshairX
                moveY = target_y - config.crosshairY
                distance = math.sqrt(moveX**2 + moveY**2)
                valid_targets.append((i, distance, moveX, moveY))
        
        # 如果有有效目標，選擇最近的一個進行瞄準
        if valid_targets:
            # 按距離排序，選擇最近的目標
            valid_targets.sort(key=lambda x: x[1])
            indexMin, _, moveX, moveY = valid_targets[0]
            
            # 應用靈敏度調整
            moveX = int(moveX // config.Sensitivity)
            moveY = int(moveY // config.Sensitivity)
            
            # 執行滑鼠移動
            for i in range(config.movementSteps):
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_MOVE, 
                    int(moveX * config.MovementCoefficientX), 
                    int(moveY * config.MovementCoefficientY), 
                    0, 0
                )
                time.sleep(config.delay)
        
        # 更新overlay顯示的框框和概率
        try:
            boxes_overlay.queue.clear()
            confidences_overlay.queue.clear()
        except:
            pass
        boxes_overlay.put(boxes)
        confidences_overlay.put(confidences)
        
    cv2.destroyAllWindows()
    overlayThread.join()
                 
if __name__ == "__main__":
    main()