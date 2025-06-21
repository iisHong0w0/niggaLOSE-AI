# main.py (FIXED)
import threading
import queue
import time
import math
import numpy as np
import cv2
import mss
import win32api
import win32con

# 根據模型類型導入不同函式庫
import onnxruntime as ort
import torch
from ultralytics import YOLO

# 從我們自己建立的模組中導入
from config import Config, load_config
from win_utils import send_mouse_move, is_key_pressed
from inference import preprocess_image, postprocess_outputs, non_max_suppression
from overlay import start_pyqt_overlay
from settings_gui import create_settings_gui

def ai_logic_loop(config, model, model_type, boxes_queue, confidences_queue):
    """AI 推理和滑鼠控制的主要循環"""
    screen_capture = mss.mss()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if model_type == 'pt':
        print(f"PyTorch 模型將在 {device} 上運行。")
        model.to(device)

    input_name = None
    if model_type == 'onnx':
        input_name = model.get_inputs()[0].name

    while config.Running:
        # --- MODIFIED: 重新設計的邏輯判斷 ---
        # 1. 如果設定了FOV跟隨滑鼠，則更新十字準星座標為滑鼠目前位置
        if config.fov_follow_mouse:
            try:
                x, y = win32api.GetCursorPos()
                config.crosshairX = x
                config.crosshairY = y
            except Exception:
                # 發生錯誤時，退回使用螢幕中心
                config.crosshairX = config.width // 2
                config.crosshairY = config.height // 2
        else:
            # 關閉FOV跟隨時自動定位到螢幕中心
            config.crosshairX = config.width // 2
            config.crosshairY = config.height // 2

        # 2. 判斷是否應該繼續執行檢測
        is_aiming = any(is_key_pressed(k) for k in config.AimKeys)
        
        # 條件：如果 (功能總開關關閉) 或者 (不是保持檢測模式 且 沒有按住自瞄鍵)
        if not config.AimToggle or (not config.keep_detecting and not is_aiming):
            # 清空繪圖佇列，避免上次的框殘留
            with boxes_queue.mutex:
                boxes_queue.queue.clear()
            boxes_queue.put([])
            time.sleep(0.1) # 降低CPU使用率
            continue
        # --- END MODIFIED ---
            
        fov_size = config.fov_size
        region = {
            "left": max(0, config.crosshairX - fov_size // 2),
            "top": max(0, config.crosshairY - fov_size // 2),
            "width": fov_size,
            "height": fov_size,
        }
        
        # 確保擷取區域不會超出螢幕範圍
        if region['left'] + region['width'] > config.width:
            region['width'] = config.width - region['left']
        if region['top'] + region['height'] > config.height:
            region['height'] = config.height - region['top']

        try:
            game_frame = np.array(screen_capture.grab(region))
        except mss.exception.ScreenShotError:
            continue

        if game_frame.size == 0:
            continue
        
        game_frame_rgb = cv2.cvtColor(game_frame, cv2.COLOR_BGRA2RGB)

        boxes, confidences = [], []
        
        if model_type == 'onnx':
            input_tensor = preprocess_image(game_frame, config.model_input_size)
            try:
                outputs = model.run(None, {input_name: input_tensor})
                boxes, confidences = postprocess_outputs(outputs, region['width'], region['height'], config.model_input_size, config.min_confidence)
                boxes, confidences = non_max_suppression(boxes, confidences)
            except Exception as e:
                print(f"ONNX 推理錯誤: {e}")
                continue
        
        elif model_type == 'pt':
            try:
                results = model(game_frame_rgb, verbose=False)
                boxes_tensor = results[0].boxes.xyxy
                confidences_tensor = results[0].boxes.conf
                high_conf_indices = confidences_tensor >= config.min_confidence
                boxes = boxes_tensor[high_conf_indices].cpu().numpy().tolist()
                confidences = confidences_tensor[high_conf_indices].cpu().numpy().tolist()
            except Exception as e:
                print(f"PyTorch 推理錯誤: {e}")
                continue

        # --- MODIFIED: 只有在按下自瞄鍵時才移動滑鼠 ---
        # 這樣 "保持檢測" 模式下就只會顯示框，不會自動瞄準
        if is_aiming:
            valid_targets = []
            absolute_boxes = []
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box
                abs_x1, abs_y1 = region['left'] + x1, region['top'] + y1
                abs_x2, abs_y2 = region['left'] + x2, region['top'] + y2
                absolute_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])

                target_x = (abs_x1 + abs_x2) / 2
                target_y = abs_y1 + (abs_y2 - abs_y1) * 0.085 if config.aim_part == "head" else (abs_y1 + abs_y2) / 2
                
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
        # --- END MODIFIED ---
        else: # 如果只是保持檢測但沒按自瞄鍵，還是要計算絕對座標用於顯示
            absolute_boxes = []
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box
                abs_x1, abs_y1 = region['left'] + x1, region['top'] + y1
                abs_x2, abs_y2 = region['left'] + x2, region['top'] + y2
                absolute_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])
        
        if boxes_queue.full():
            try: boxes_queue.get_nowait()
            except queue.Empty: pass
        if confidences_queue.full():
            try: confidences_queue.get_nowait()
            except queue.Empty: pass
            
        boxes_queue.put(absolute_boxes)
        confidences_queue.put(confidences)

        time.sleep(config.detect_interval)

# --- MODIFIED: 補全 auto_fire_loop 函式 ---
def auto_fire_loop(config, boxes_queue):
    """自動開火功能的獨立循環"""
    last_key_state = False
    delay_start_time = None
    
    while config.Running:
        time.sleep(0.006) # 循環延遲
        key_state = is_key_pressed(config.auto_fire_key)

        if key_state and not last_key_state:
            delay_start_time = time.time()
        
        if key_state:
            if delay_start_time and (time.time() - delay_start_time >= config.auto_fire_delay):
                latest_boxes = []
                while not boxes_queue.empty():
                    try:
                        latest_boxes = boxes_queue.get_nowait()
                    except queue.Empty:
                        break
                
                boxes = latest_boxes
                
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)
                    if x1 <= config.crosshairX <= x2 and y1 <= config.crosshairY <= y2:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        time.sleep(0.01)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        break
        else:
            delay_start_time = None

        last_key_state = key_state
# --- END MODIFIED ---

def aim_toggle_key_listener(config, update_gui_callback=None):
    """持續監聽自動瞄準開關快捷鍵，按下時切換 AimToggle 狀態"""
    import win32api
    last_state = False
    while True:
        key_code = getattr(config, 'aim_toggle_key', 0x2D)  # 預設 INS
        state = win32api.GetAsyncKeyState(key_code) & 0x8000
        if state and not last_state:
            config.AimToggle = not config.AimToggle
            print(f"[快捷鍵] 自動瞄準狀態已切換為: {config.AimToggle}")
            if update_gui_callback:
                update_gui_callback(config.AimToggle)
        last_state = state
        time.sleep(0.05)


if __name__ == "__main__":
    config = Config()
    load_config(config)

    # 移除啟動時自動載入模型與 AI 執行緒
    # 由 GUI 控制模型載入與 AI 執行緒啟動
    ai_thread = None
    auto_fire_thread = None
    boxes_queue = queue.Queue(maxsize=2)
    confidences_queue = queue.Queue(maxsize=2)

    def start_ai_threads(model_path):
        """由 GUI 呼叫，根據模型路徑載入模型並啟動 AI 執行緒"""
        global ai_thread, auto_fire_thread
        # 停止舊執行緒
        config.Running = False
        time.sleep(0.1)
        config.Running = True
        model = None
        model_type = ''
        if model_path.endswith('.onnx'):
            model_type = 'onnx'
            try:
                print(f"正在載入 ONNX 模型: {model_path}")
                providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
                model = ort.InferenceSession(model_path, providers=providers)
                provider = model.get_providers()[0]
                config.current_provider = provider
                print(f"ONNX 模型載入成功，使用: {provider}")
            except Exception as e:
                print(f"載入 ONNX 模型失敗: {e}")
                return False
        elif model_path.endswith('.pt'):
            model_type = 'pt'
            try:
                print(f"正在載入 PyTorch 模型: {model_path}")
                model = YOLO(model_path)
                model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
                print("PyTorch 模型載入成功。")
            except Exception as e:
                print(f"載入 PyTorch 模型失敗: {e}")
                return False
        else:
            print(f"錯誤: 不支援的模型格式: {model_path}")
            return False
        # 啟動新執行緒
        ai_thread = threading.Thread(
            target=ai_logic_loop,
            args=(config, model, model_type, boxes_queue, confidences_queue),
            daemon=True
        )
        ai_thread.start()
        auto_fire_thread = threading.Thread(target=auto_fire_loop, args=(config, boxes_queue), daemon=True)
        auto_fire_thread.start()
        print("AI 執行緒已啟動。")
        return True

    # 啟動自動瞄準開關快捷鍵監聽執行緒
    threading.Thread(target=aim_toggle_key_listener, args=(config,), daemon=True).start()

    # 啟動 GUI，並將 start_ai_threads 傳給 GUI 以便選單切換時呼叫
    settings_thread = threading.Thread(target=create_settings_gui, args=(config, start_ai_threads), daemon=True)
    settings_thread.start()

    print("啟動 Overlay... 所有模組已開始運作。")
    start_pyqt_overlay(boxes_queue, confidences_queue, config)