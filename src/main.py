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
import winsound  # ***** 新增：音效模組 *****
import os
import psutil  # ***** 新增：進程優化模組 *****
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

def optimize_cpu_performance(config):
    """優化CPU性能設定"""
    if not getattr(config, 'cpu_optimization', True):
        return
    
    try:
        # 獲取當前進程
        current_process = psutil.Process()
        
        # 設定進程優先級 (Windows 專用)
        if sys.platform == "win32":
            process_priority = getattr(config, 'process_priority', 'high')
            try:
                if process_priority == 'realtime':
                    current_process.nice(psutil.REALTIME_PRIORITY_CLASS)
                    print("[性能優化] 設定進程優先級為：實時")
                elif process_priority == 'high':
                    current_process.nice(psutil.HIGH_PRIORITY_CLASS)
                    print("[性能優化] 設定進程優先級為：高")
                else:
                    current_process.nice(psutil.NORMAL_PRIORITY_CLASS)
                    print("[性能優化] 設定進程優先級為：正常")
            except Exception as e:
                print(f"[性能優化] 設定進程優先級失敗：{e}")
        else:
            print("[性能優化] 非Windows系統，跳過進程優先級設定")
        
        # 設定CPU親和性
        cpu_affinity = getattr(config, 'cpu_affinity', None)
        if cpu_affinity is not None:
            current_process.cpu_affinity(cpu_affinity)
            print(f"[性能優化] 設定CPU親和性為：{cpu_affinity}")
        else:
            # 使用所有可用CPU核心
            all_cpus = list(range(psutil.cpu_count()))
            current_process.cpu_affinity(all_cpus)
            print(f"[性能優化] 使用所有CPU核心：{all_cpus}")
        
        # 設定線程優先級函數
        def set_thread_priority(thread_priority='high'):
            try:
                import win32process
                import win32api
                
                if thread_priority == 'realtime':
                    win32process.SetThreadPriority(win32api.GetCurrentThread(), win32process.THREAD_PRIORITY_TIME_CRITICAL)
                elif thread_priority == 'high':
                    win32process.SetThreadPriority(win32api.GetCurrentThread(), win32process.THREAD_PRIORITY_HIGHEST)
                else:
                    win32process.SetThreadPriority(win32api.GetCurrentThread(), win32process.THREAD_PRIORITY_NORMAL)
            except Exception as e:
                print(f"[性能優化] 設定線程優先級失敗：{e}")
        
        # 返回線程優先級設定函數
        return set_thread_priority
        
    except Exception as e:
        print(f"[性能優化] CPU性能優化失敗：{e}")
        return None

def optimize_onnx_session(config):
    """優化ONNX運行時設定"""
    try:
        # 設定ONNX運行時選項
        session_options = ort.SessionOptions()
        
        # 啟用所有優化
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # 設定線程數量為CPU核心數
        session_options.intra_op_num_threads = psutil.cpu_count()
        session_options.inter_op_num_threads = psutil.cpu_count()
        
        # 啟用並行執行
        session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        
        # 啟用記憶體優化
        session_options.enable_mem_pattern = True
        session_options.enable_cpu_mem_arena = True
        
        print(f"[性能優化] ONNX使用 {psutil.cpu_count()} 個CPU核心")
        return session_options
        
    except Exception as e:
        print(f"[性能優化] ONNX優化失敗：{e}")
        return None



def ai_logic_loop(config, model, model_type, boxes_queue, confidences_queue):
    """AI 推理和滑鼠控制的主要循環"""
    # 設定線程優先級
    set_thread_priority = optimize_cpu_performance(config)
    if set_thread_priority:
        thread_priority = getattr(config, 'thread_priority', 'high')
        set_thread_priority(thread_priority)
        print(f"[性能優化] AI線程優先級設定為：{thread_priority}")
    
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
    
    # ***** 新增：音效提示相關變數 *****
    last_sound_time = 0
    sound_playing = False
    
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
        if config.fov_follow_mouse:
            try:
                x, y = win32api.GetCursorPos()
                config.crosshairX, config.crosshairY = x, y
            except Exception:
                config.crosshairX, config.crosshairY = half_width, half_height
        else:
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
        
        # 修改：檢測整個畫面而不是只檢測FOV區域
        region = {
            "left": 0,
            "top": 0,
            "width": config.width, 
            "height": config.height,
        }

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

        # 修改：由於檢測整個畫面，boxes已經是絕對座標，不需要轉換
        absolute_boxes = boxes[:]
        
        # 新增：FOV過濾邏輯 - 只保留與FOV框有交集的人物框
        # 改進：檢測整個畫面後，使用FOV框進行過濾
        # 只要人物框與FOV框有任何重疊就會被保留（不需要完全包含）
        if absolute_boxes:
            fov_half = fov_size // 2
            fov_left = crosshair_x - fov_half
            fov_top = crosshair_y - fov_half
            fov_right = crosshair_x + fov_half
            fov_bottom = crosshair_y + fov_half
            
            filtered_boxes = []
            filtered_confidences = []
            
            for i, box in enumerate(absolute_boxes):
                x1, y1, x2, y2 = box
                # 矩形交集檢測：只要人物框有一點點碰到FOV框就算
                # 條件：人物框左邊 < FOV右邊 且 人物框右邊 > FOV左邊 且
                #       人物框上邊 < FOV下邊 且 人物框下邊 > FOV上邊
                if (x1 < fov_right and x2 > fov_left and 
                    y1 < fov_bottom and y2 > fov_top):
                    filtered_boxes.append(box)
                    if i < len(confidences):
                        filtered_confidences.append(confidences[i])
            
            absolute_boxes = filtered_boxes
            confidences = filtered_confidences

        # ***** 新增：單目標模式 - 只保留離準心最近的一個目標 *****
        if config.single_target_mode and absolute_boxes:
            crosshair_x, crosshair_y = config.crosshairX, config.crosshairY
            closest_box = None
            min_distance = float('inf')
            closest_confidence = 0
            
            for i, box in enumerate(absolute_boxes):
                abs_x1, abs_y1, abs_x2, abs_y2 = box
                # 計算邊界框中心點距離準心的距離
                box_center_x = (abs_x1 + abs_x2) * 0.5
                box_center_y = (abs_y1 + abs_y2) * 0.5
                distance = math.sqrt((box_center_x - crosshair_x)**2 + (box_center_y - crosshair_y)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_box = box
                    closest_confidence = confidences[i] if i < len(confidences) else 0.5
            
            # 只保留最近的一個目標
            if closest_box:
                absolute_boxes = [closest_box]
                confidences = [closest_confidence]
            else:
                absolute_boxes = []
                confidences = []

        # ***** 新增：音效提示系統 - 檢測準心是否在敵人框內 *****
        if not config.single_target_mode or not absolute_boxes:
            crosshair_x, crosshair_y = config.crosshairX, config.crosshairY
        target_detected = False
        
        if config.enable_sound_alert and absolute_boxes:
            for box in absolute_boxes:
                abs_x1, abs_y1, abs_x2, abs_y2 = box
                # 檢查準心是否在敵人框內
                if abs_x1 <= crosshair_x <= abs_x2 and abs_y1 <= crosshair_y <= abs_y2:
                    target_detected = True
                    break
            
            # 音效播放邏輯
            if target_detected:
                # 檢查音效間隔，避免過於頻繁播放
                if current_time - last_sound_time >= config.sound_interval / 1000.0:
                    try:
                        # 異步播放音效，避免阻塞主線程
                        threading.Thread(
                            target=winsound.Beep, 
                            args=(config.sound_frequency, config.sound_duration),
                            daemon=True
                        ).start()
                        last_sound_time = current_time
                    except Exception as e:
                        pass  # 忽略音效播放錯誤

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
                    # 直接使用mouse_event
                    send_mouse_move(int(dx), int(dy), method="delayed")
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
        # 在性能模式下進一步優化睡眠時間
        if getattr(config, 'performance_mode', False):
            # 極短睡眠時間以最大化CPU使用率
            sleep_time = max(config.detect_interval, 0.0001)  # 最小0.1ms
        else:
            sleep_time = config.detect_interval
        time.sleep(sleep_time)

def auto_fire_loop(config, boxes_queue):
    """自動開火功能的獨立循環 - 修復按鍵更新問題"""
    # 設定線程優先級
    set_thread_priority = optimize_cpu_performance(config)
    if set_thread_priority:
        thread_priority = getattr(config, 'thread_priority', 'high')
        set_thread_priority(thread_priority)
        print(f"[性能優化] 自動開火線程優先級設定為：{thread_priority}")
    
    last_key_state = False
    delay_start_time = None
    last_fire_time = 0
    cached_boxes = []
    last_box_update = 0
    
    # 優化參數 - 根據檢測間隔調整
    BOX_UPDATE_INTERVAL = max(0.005, config.detect_interval)  # 更積極的更新間隔
    KEY_CHECK_INTERVAL = 0.001  # 進一步降低按鍵檢查間隔
    
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
        
        # 優化：動態睡眠時間，在性能模式下進一步優化
        if getattr(config, 'performance_mode', False):
            sleep_time = KEY_CHECK_INTERVAL if key_state else 0.002  # 性能模式下更短的睡眠時間
        else:
            sleep_time = KEY_CHECK_INTERVAL if key_state else 0.008
        time.sleep(sleep_time)



def aim_toggle_key_listener(config, update_gui_callback=None):
    """持續監聽自動瞄準開關快捷鍵 - 優化版本"""
    # 設定線程優先級
    set_thread_priority = optimize_cpu_performance(config)
    if set_thread_priority:
        thread_priority = getattr(config, 'thread_priority', 'high')
        set_thread_priority(thread_priority)
        print(f"[性能優化] 快捷鍵監聽線程優先級設定為：{thread_priority}")
    
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
    sleep_interval = 0.01 if performance_mode else 0.03  # 性能模式下更頻繁檢查
    
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
    
    # 在程序開始時優化CPU性能
    print("[性能優化] 正在優化CPU性能設定...")
    optimize_cpu_performance(config)
    print("[性能優化] ✓ CPU性能優化完成")

    # 優化：使用配置中的隊列大小設置
    max_queue_size = getattr(config, 'max_queue_size', 3)
    boxes_queue = queue.Queue(maxsize=max_queue_size)
    confidences_queue = queue.Queue(maxsize=max_queue_size)

    def start_ai_threads(model_path):
        """由 GUI 呼叫，載入模型並啟動/重啟 AI 執行緒"""
        global ai_thread, auto_fire_thread, config
        
        # 停止現有線程
        if ai_thread is not None and ai_thread.is_alive():
            config.Running = False
            ai_thread.join()
            if auto_fire_thread is not None:
                auto_fire_thread.join()

        config.Running = True
        
        model, model_type = None, ''
        if model_path.endswith('.onnx'):
            model_type = 'onnx'
            try:
                print(f"正在載入 ONNX 模型: {model_path}")
                providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
                
                # 獲取優化的會話選項
                session_options = optimize_onnx_session(config)
                if session_options:
                    model = ort.InferenceSession(model_path, providers=providers, sess_options=session_options)
                    print(f"[性能優化] ONNX 模型已使用優化設定載入")
                else:
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
        
        ai_thread.start()
        auto_fire_thread.start()
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