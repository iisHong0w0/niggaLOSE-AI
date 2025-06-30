# main.py
import threading
import queue
import time
import math
import numpy as np
import cv2
import mss
import win32api
import win32con
import sys
from typing import Optional

# 根據模型類型導入不同函式庫
import onnxruntime as ort
import torch
from ultralytics import YOLO

# 從我們自己建立的模組中導入
from config import Config, load_config
from win_utils import send_mouse_move, is_key_pressed
from inference import preprocess_image, postprocess_outputs, non_max_suppression, PIDController
from overlay import start_pyqt_overlay, PyQtOverlay
from settings_gui import create_settings_gui
from status_panel import StatusPanel # ***** 新增此行 *****
from scaling_warning_dialog import check_windows_scaling # ***** 新增此行 *****



# 全域變數宣告
ai_thread: Optional[threading.Thread] = None
auto_fire_thread: Optional[threading.Thread] = None
anti_recoil_thread: Optional[threading.Thread] = None



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
        
    pid_x = PIDController(config.pid_kp_x, config.pid_ki_x, config.pid_kd_x)
    pid_y = PIDController(config.pid_kp_y, config.pid_ki_y, config.pid_kd_y)

    # 優化：緩存配置項，減少屬性訪問
    last_pid_update = 0
    pid_check_interval = 1.0  # 每秒檢查一次PID參數變化
    
    # 優化：預計算常用值
    half_width = config.width // 2
    half_height = config.height // 2

    while config.Running:
        current_time = time.time()
        
        # 優化：降低PID參數檢查頻率
        if current_time - last_pid_update > pid_check_interval:
            pid_x.Kp, pid_x.Ki, pid_x.Kd = config.pid_kp_x, config.pid_ki_x, config.pid_kd_x
            pid_y.Kp, pid_y.Ki, pid_y.Kd = config.pid_kp_y, config.pid_ki_y, config.pid_kd_y
            last_pid_update = current_time
        
        # 優化：緩存十字準心位置計算
        if config.fov_follow_mouse and not config.enable_anti_recoil:
            try:
                x, y = win32api.GetCursorPos()
                config.crosshairX, config.crosshairY = x, y
            except Exception:
                config.crosshairX, config.crosshairY = half_width, half_height
        else:
            if not config.enable_anti_recoil:
                config.crosshairX, config.crosshairY = half_width, half_height

        # 優化：一次性檢查所有瞄準鍵
        is_aiming = any(is_key_pressed(k) for k in config.AimKeys)
        
        if not config.AimToggle or (not config.keep_detecting and not is_aiming):
            # 優化：批量清空隊列，避免重複操作
            try:
                while not boxes_queue.empty():
                    boxes_queue.get_nowait()
                while not confidences_queue.empty():
                    confidences_queue.get_nowait()
            except queue.Empty:
                pass
            boxes_queue.put([])
            confidences_queue.put([])
            time.sleep(0.05)  # 優化：非活動時使用較長睡眠
            continue
            
        fov_size = config.fov_size
        crosshair_x, crosshair_y = config.crosshairX, config.crosshairY
        
        # 優化：預計算FOV區域
        fov_half = fov_size // 2
        region = {
            "left": max(0, crosshair_x - fov_half),
            "top": max(0, crosshair_y - fov_half),
            "width": fov_size, 
            "height": fov_size,
        }
        
        # 優化：邊界檢查
        if region['left'] + region['width'] > config.width: 
            region['width'] = config.width - region['left']
        if region['top'] + region['height'] > config.height: 
            region['height'] = config.height - region['top']

        try:
            game_frame = np.array(screen_capture.grab(region))
        except Exception:
            continue
        if game_frame.size == 0: 
            continue
        
        # 優化：只在需要時進行顏色轉換
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
            game_frame_rgb = cv2.cvtColor(game_frame, cv2.COLOR_BGRA2RGB)
            try:
                results = model(game_frame_rgb, verbose=False)
                high_conf_indices = results[0].boxes.conf >= config.min_confidence
                boxes = results[0].boxes.xyxy[high_conf_indices].cpu().numpy().tolist()
                confidences = results[0].boxes.conf[high_conf_indices].cpu().numpy().tolist()
            except Exception as e:
                print(f"PyTorch 推理錯誤: {e}")
                continue

        # 優化：使用列表推導式進行座標轉換
        absolute_boxes = [
            [region['left'] + x1, region['top'] + y1, region['left'] + x2, region['top'] + y2]
            for x1, y1, x2, y2 in boxes
        ]

        if is_aiming and absolute_boxes:
            # 優化：預計算瞄準參數
            aim_part = config.aim_part
            head_height_ratio = config.head_height_ratio
            head_width_ratio = config.head_width_ratio
            body_width_ratio = config.body_width_ratio
            
            valid_targets = []
            for box in absolute_boxes:
                abs_x1, abs_y1, abs_x2, abs_y2 = box
                box_w, box_h = abs_x2 - abs_x1, abs_y2 - abs_y1
                box_center_x = abs_x1 + box_w * 0.5
                
                # 優化：統一的瞄準部位計算
                if aim_part == "head":
                    target_x = box_center_x
                    target_y = abs_y1 + box_h * head_height_ratio * 0.5
                else: # "body"
                    target_x = box_center_x
                    head_h = box_h * head_height_ratio
                    target_y = (abs_y1 + head_h + abs_y2) * 0.5

                moveX = target_x - crosshair_x
                moveY = target_y - crosshair_y
                distance = math.sqrt(moveX*moveX + moveY*moveY)  # 優化：避免**運算
                valid_targets.append((distance, moveX, moveY))

            if valid_targets:
                valid_targets.sort(key=lambda x: x[0])
                _, errorX, errorY = valid_targets[0]
                dx, dy = pid_x.update(errorX), pid_y.update(errorY)
                if abs(dx) > 0 or abs(dy) > 0:
                    send_mouse_move(int(dx), int(dy))
            else:
                pid_x.reset()
                pid_y.reset()
        else:
            pid_x.reset()
            pid_y.reset()

        # 優化：改善隊列管理，避免重複檢查
        try:
            if boxes_queue.full():
                boxes_queue.get_nowait()
            if confidences_queue.full():
                confidences_queue.get_nowait()
        except queue.Empty:
            pass
            
        boxes_queue.put(absolute_boxes)
        confidences_queue.put(confidences)

        # 優化：使用配置的檢測間隔，確保一致性
        time.sleep(config.detect_interval)

def auto_fire_loop(config, boxes_queue):
    """自動開火功能的獨立循環 - 修復按鍵更新問題"""
    last_key_state = False
    delay_start_time = None
    last_fire_time = 0
    cached_boxes = []
    last_box_update = 0
    
    # 優化參數 - 根據檢測間隔調整
    BOX_UPDATE_INTERVAL = max(0.015, config.detect_interval)  # 與檢測間隔同步
    KEY_CHECK_INTERVAL = 0.003  # 降低按鍵檢查間隔
    
    # 修復：動態更新按鍵配置
    auto_fire_key = config.auto_fire_key
    auto_fire_key2 = getattr(config, 'auto_fire_key2', None)
    last_key_update = 0
    key_update_interval = 0.5  # 每0.5秒檢查一次按鍵配置變化
    
    while config.Running:
        current_time = time.time()
        
        # 修復：定期更新按鍵配置，允許動態更改
        if current_time - last_key_update > key_update_interval:
            auto_fire_key = config.auto_fire_key
            auto_fire_key2 = getattr(config, 'auto_fire_key2', None)
            last_key_update = current_time
        
        # 使用更新後的按鍵配置
        key_state = is_key_pressed(auto_fire_key)
        if auto_fire_key2:
            key_state = key_state or is_key_pressed(auto_fire_key2)

        # 處理按鍵狀態變化
        if key_state and not last_key_state:
            delay_start_time = current_time
        
        if key_state:
            # 檢查開鏡延遲
            if delay_start_time and (current_time - delay_start_time >= config.auto_fire_delay):
                # 檢查射擊冷卻時間
                if current_time - last_fire_time >= config.auto_fire_interval:
                    
                    # 優化：動態調整boxes更新頻率
                    if current_time - last_box_update >= BOX_UPDATE_INTERVAL:
                        try:
                            # 修復：透過直接存取底層 deque 來「偷看」最新項目，而不是消耗它。
                            # 這樣可以防止自動開火線程與UI繪圖線程競爭框體數據，解決UI卡頓問題。
                            if not boxes_queue.empty():
                                cached_boxes = boxes_queue.queue[-1]
                                last_box_update = current_time
                        except IndexError:
                            # 在多線程環境下，即使檢查過 not empty，隊列仍可能在訪問前變空。
                            # 這種情況下，我們什麼都不做，繼續使用舊的 cached_boxes。
                            pass
                    
                    # 優化：預計算瞄準參數
                    if cached_boxes:
                        crosshair_x, crosshair_y = config.crosshairX, config.crosshairY
                        target_part = config.auto_fire_target_part
                        head_height_ratio = config.head_height_ratio
                        head_width_ratio = config.head_width_ratio
                        body_width_ratio = config.body_width_ratio
                        
                        # 快速射擊判斷
                        should_fire = False
                        for box in cached_boxes:
                            x1, y1, x2, y2 = box
                            box_w, box_h = x2 - x1, y2 - y1
                            box_center_x = x1 + box_w * 0.5
                            
                            # 優化：快速邊界檢查
                            if target_part == "head":
                                head_h = box_h * head_height_ratio
                                head_w = box_w * head_width_ratio
                                head_x1 = box_center_x - head_w * 0.5
                                head_x2 = box_center_x + head_w * 0.5
                                head_y2 = y1 + head_h
                                should_fire = (head_x1 <= crosshair_x <= head_x2 and y1 <= crosshair_y <= head_y2)
                            elif target_part == "body":
                                body_w = box_w * body_width_ratio
                                body_x1 = box_center_x - body_w * 0.5
                                body_x2 = box_center_x + body_w * 0.5
                                body_y1 = y1 + box_h * head_height_ratio
                                should_fire = (body_x1 <= crosshair_x <= body_x2 and body_y1 <= crosshair_y <= y2)
                            elif target_part == "both":
                                # 快速計算頭部和身體區域
                                head_h = box_h * head_height_ratio
                                head_w = box_w * head_width_ratio
                                head_x1 = box_center_x - head_w * 0.5
                                head_x2 = box_center_x + head_w * 0.5
                                
                                is_in_head = (head_x1 <= crosshair_x <= head_x2 and y1 <= crosshair_y <= y1 + head_h)
                                
                                if not is_in_head:
                                    body_w = box_w * body_width_ratio
                                    body_x1 = box_center_x - body_w * 0.5
                                    body_x2 = box_center_x + body_w * 0.5
                                    body_y1 = y1 + head_h
                                    is_in_body = (body_x1 <= crosshair_x <= body_x2 and body_y1 <= crosshair_y <= y2)
                                    should_fire = is_in_body
                                else:
                                    should_fire = True

                            if should_fire:
                                # 快速射擊
                                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                last_fire_time = current_time
                                break
        else:
            delay_start_time = None
            # 優化：按鍵未按下時清空緩存
            if cached_boxes:
                cached_boxes = []

        last_key_state = key_state
        
        # 優化：動態睡眠時間
        sleep_time = KEY_CHECK_INTERVAL if key_state else 0.008
        time.sleep(sleep_time)

def anti_recoil_loop(config):
    """防後座力功能循環，在按住左鍵時向上移動FOV - 優化版本"""
    original_crosshair_y = config.height // 2
    was_pressing = False
    last_check_time = 0
    
    # 優化：預計算睡眠間隔
    performance_mode = getattr(config, 'performance_mode', False)
    active_sleep = 0.008 if performance_mode else 0.01
    inactive_sleep = 0.05 if performance_mode else 0.1
    
    while config.Running:
        current_time = time.time()
        
        if not config.enable_anti_recoil:
            if was_pressing:
                config.crosshairY = original_crosshair_y
                was_pressing = False
            time.sleep(inactive_sleep)
            continue

        # 優化：減少按鍵檢測頻率，除非在性能模式下
        if not performance_mode and (current_time - last_check_time < 0.008):
            time.sleep(0.001)
            continue
        
        last_check_time = current_time
        is_pressing = is_key_pressed(0x01)

        if is_pressing and not was_pressing:
            original_crosshair_y = config.crosshairY
        
        if is_pressing:
            config.crosshairY -= config.anti_recoil_speed
            config.crosshairY = max(0, int(config.crosshairY))
            time.sleep(active_sleep)
        elif not is_pressing and was_pressing:
            config.crosshairY = original_crosshair_y
            time.sleep(active_sleep)
        else:
            time.sleep(inactive_sleep)
            
        was_pressing = is_pressing

def aim_toggle_key_listener(config, update_gui_callback=None):
    """持續監聽自動瞄準開關快捷鍵 - 優化版本"""
    last_state = False
    key_code = getattr(config, 'aim_toggle_key', 0x78)  # 默認 F9 鍵
    
    # 獲取按鍵名稱
    from win_utils import get_vk_name
    key_name = get_vk_name(key_code)
    print(f"[快捷鍵監聽] 開始監聽快捷鍵: {key_name} (0x{key_code:02X})")
    print(f"[快捷鍵監聽] 當前自動瞄準狀態: {config.AimToggle}")
    print(f"[快捷鍵監聽] 按下 {key_name} 來切換自動瞄準功能")
    
    # 優化：預計算睡眠時間
    performance_mode = getattr(config, 'performance_mode', False)
    sleep_interval = 0.03 if performance_mode else 0.05  # 性能模式下更頻繁檢查
    
    # 調試計數器
    debug_counter = 0
    
    while config.Running:
        try:
            # 重新獲取快捷鍵設置（可能在 GUI 中被更改）
            current_key_code = getattr(config, 'aim_toggle_key', 0x78)
            if current_key_code != key_code:
                key_code = current_key_code
                key_name = get_vk_name(key_code)
                print(f"[快捷鍵監聽] 快捷鍵已更新為: {key_name} (0x{key_code:02X})")
            
            # 檢測按鍵狀態
            state = bool(win32api.GetAsyncKeyState(key_code) & 0x8000)
            
            # 檢測按鍵按下事件（從未按下到按下的轉換）
            if state and not last_state:
                old_state = config.AimToggle
                config.AimToggle = not config.AimToggle
                print(f"[快捷鍵] ✓ 檢測到 {key_name} 按下！自動瞄準: {old_state} → {config.AimToggle}")
                
                if update_gui_callback:
                    update_gui_callback(config.AimToggle)
            
            last_state = state
            
            # 每30秒輸出一次狀態報告
            debug_counter += 1
            if debug_counter % (30 * (1.0 / sleep_interval)) == 0:
                print(f"[快捷鍵監聽] 運行中... 當前監聽: {key_name}, 自動瞄準: {config.AimToggle}")
            
        except Exception as e:
            print(f"[快捷鍵監聽] 錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        # 優化：根據性能模式調整睡眠時間
        time.sleep(sleep_interval)

if __name__ == "__main__":
    # 在程序開始時檢測 Windows 縮放比例
    print("[系統檢測] 正在檢測 Windows 縮放設定...")
    if not check_windows_scaling():
        print("[系統檢測] 程序因縮放設定問題而退出")
        sys.exit(1)
    print("[系統檢測] ✓ 縮放設定檢測通過")
    
    config = Config()
    load_config(config)

    # 優化：使用配置中的隊列大小設置
    max_queue_size = getattr(config, 'max_queue_size', 3)
    boxes_queue = queue.Queue(maxsize=max_queue_size)
    confidences_queue = queue.Queue(maxsize=max_queue_size)

    def start_ai_threads(model_path):
        """由 GUI 呼叫，載入模型並啟動/重啟 AI 執行緒"""
        global ai_thread, auto_fire_thread, anti_recoil_thread, config
        
        # 停止現有線程
        if ai_thread is not None and ai_thread.is_alive():
            config.Running = False
            ai_thread.join()
            if auto_fire_thread is not None:
                auto_fire_thread.join()
            if anti_recoil_thread is not None:
                anti_recoil_thread.join()

        config.Running = True
        
        model, model_type = None, ''
        if model_path.endswith('.onnx'):
            model_type = 'onnx'
            try:
                print(f"正在載入 ONNX 模型: {model_path}")
                providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
                model = ort.InferenceSession(model_path, providers=providers)
                config.current_provider = model.get_providers()[0]
                print(f"ONNX 模型載入成功，使用: {config.current_provider}")
            except Exception as e:
                print(f"載入 ONNX 模型失敗: {e}"); return False
        elif model_path.endswith('.pt'):
            model_type = 'pt'
            try:
                print(f"正在載入 PyTorch 模型: {model_path}")
                model = YOLO(model_path)
                model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False) # 預熱
                print("PyTorch 模型載入成功。")
            except Exception as e:
                print(f"載入 PyTorch 模型失敗: {e}"); return False
        else:
            print(f"錯誤: 不支援的模型格式: {model_path}"); return False

        ai_thread = threading.Thread(target=ai_logic_loop, args=(config, model, model_type, boxes_queue, confidences_queue), daemon=True)
        auto_fire_thread = threading.Thread(target=auto_fire_loop, args=(config, boxes_queue), daemon=True)
        anti_recoil_thread = threading.Thread(target=anti_recoil_loop, args=(config,), daemon=True)
        
        ai_thread.start()
        auto_fire_thread.start()
        anti_recoil_thread.start()
        print("AI 相關執行緒已啟動。")
        return True

    # 啟動設置 GUI
    settings_thread = threading.Thread(target=create_settings_gui, args=(config, start_ai_threads), daemon=True)
    settings_thread.start()
    
    # 確保配置完全載入後再啟動快捷鍵監聽
    print(f"[初始化] 配置載入完成，快捷鍵設置: {getattr(config, 'aim_toggle_key', 'None')}")
    time.sleep(0.5)  # 等待 GUI 完全初始化
    
    # 啟動快捷鍵監聽（在 GUI 啟動後）
    toggle_thread = threading.Thread(target=aim_toggle_key_listener, args=(config,), daemon=True)
    toggle_thread.start()
    print("[初始化] 快捷鍵監聽線程已啟動")

    print("啟動 Overlays... 所有模組已開始運作。")
    
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # 建立並顯示主要的繪圖覆蓋層 (人物框, FOV)
    main_overlay = PyQtOverlay(boxes_queue, confidences_queue, config)
    main_overlay.show()

    # 建立並顯示新的狀態面板
    status_panel = StatusPanel(config)
    status_panel.show()
    
    # 啟動 PyQt 應用程式事件循環，這會管理所有 PyQt 視窗
    sys.exit(app.exec())