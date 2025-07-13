# config.py
import ctypes
import json
import os

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

        # 程式執行狀態
        self.Running = True
        self.AimToggle = True
        
        # ONNX 模型相關設定
        self.model_input_size = 640
        default_model_name = 'Rivals.onnx'
        self.model_path = os.path.join('模型', default_model_name)
        self.current_provider = "CPUExecutionProvider"

        # 瞄準與顯示設定
        self.AimKeys = [0x01, 0x06, 0x02]  # 左鍵 + X2鍵 + 右鍵
        self.fov_size = 666
        self.show_confidence = True
        self.min_confidence = 0.66
        self.aim_part = "head"
        
        # ***** 新增：單目標模式 *****
        self.single_target_mode = True  # 一次最多檢測一個離準心最近的敵人
        
        # ***** 新增：音效提示系統 *****
        self.enable_sound_alert = True  # 啟用音效提示
        self.sound_frequency = 1000     # 音效頻率 (Hz)
        self.sound_duration = 100       # 音效持續時間 (ms)
        self.sound_interval = 200       # 音效間隔 (ms)
        
        # 頭部和身體區域占比設定
        self.head_width_ratio = 0.38    # 頭部寬度占檢測框寬度的比例
        self.head_height_ratio = 0.26   # 頭部高度占檢測框高度的比例
        self.body_width_ratio = 0.87     # 身體寬度占檢測框寬度的比例
        
        # PID 控制器參數 (分離 X 和 Y 軸)
        self.pid_kp_x = 0.26      # 水平 P: 比例 - 主要影響反應速度
        self.pid_ki_x = 0.0       # 水平 I: 積分 - 修正靜態誤差
        self.pid_kd_x = 0.0       # 水平 D: 微分 - 抑制抖動與過衝
        self.pid_kp_y = 0.26      # 垂直 P: 比例
        self.pid_ki_y = 0.0       # 垂直 I: 積分
        self.pid_kd_y = 0.0       # 垂直 D: 微分

        # 新增：勻速移動模式
        self.constant_speed_mode = False  # 是否使用勻速移動而非PID控制
        self.constant_speed_x = 2.0       # 水平勻速移動速度
        self.constant_speed_y = 2.0       # 垂直勻速移動速度
        
        # 新增：滑鼠移動方式選擇
        self.mouse_move_method = "delayed"  # 固定使用mouse_event

        # 優化：調整檢測間隔為更合理的值，平衡性能和響應速度
        self.detect_interval = 0.001  # 1ms間隔，極高響應速度 (優化CPU性能)
        self.aim_toggle_key = 45  # Insert 鍵
        self.auto_fire_key2 = 0x04  # 滑鼠中鍵
        
        # 自動開槍
        self.auto_fire_key = 0x06   # 滑鼠X2鍵
        self.auto_fire_delay = 0.0  # 無延遲
        self.auto_fire_interval = 0.18 # 射擊間隔
        self.auto_fire_target_part = "both" # 可選: "head", "body", "both"

        # 保持檢測功能
        self.keep_detecting = True  # 啟用保持檢測
        # FOV 跟隨鼠標
        self.fov_follow_mouse = False
        


        # 顯示開關
        self.show_fov = True
        self.show_boxes = True
        self.show_status_panel = True # ***** 新增此行 *****
        
        # 優化：性能相關設置
        self.performance_mode = True  # 預設啟用性能模式，最大化CPU使用率
        self.max_queue_size = 1  # 減少隊列大小，降低延遲
        
        # 新增：CPU性能優化參數
        self.cpu_optimization = True  # 啟用CPU優化
        self.thread_priority = "high"  # 線程優先級：normal, high, realtime
        self.process_priority = "high"  # 進程優先級：normal, high, realtime
        self.cpu_affinity = None  # CPU親和性設定，None表示使用所有CPU核心
        
        # 新增：高級/簡單模式切換
        self.advanced_mode = True  # True=高級模式，False=簡單模式

def save_config(config_instance):
    """將所有可配置的參數儲存到 config.json"""
    data = {
        'fov_size': config_instance.fov_size,
        'pid_kp_x': getattr(config_instance, 'pid_kp_x', 0.26),
        'pid_ki_x': getattr(config_instance, 'pid_ki_x', 0.0),
        'pid_kd_x': getattr(config_instance, 'pid_kd_x', 0.0),
        'pid_kp_y': getattr(config_instance, 'pid_kp_y', 0.26),
        'pid_ki_y': getattr(config_instance, 'pid_ki_y', 0.0),
        'pid_kd_y': getattr(config_instance, 'pid_kd_y', 0.0),
        'aim_part': config_instance.aim_part,
        'AimKeys': config_instance.AimKeys,
        'auto_fire_key': getattr(config_instance, 'auto_fire_key', 0x06),
        'auto_fire_delay': getattr(config_instance, 'auto_fire_delay', 0.0),
        'auto_fire_interval': getattr(config_instance, 'auto_fire_interval', 0.18),
        'auto_fire_target_part': getattr(config_instance, 'auto_fire_target_part', "both"),
        'min_confidence': config_instance.min_confidence,
        'show_confidence': config_instance.show_confidence,
        'detect_interval': config_instance.detect_interval,
        'keep_detecting': getattr(config_instance, 'keep_detecting', True),
        'fov_follow_mouse': getattr(config_instance, 'fov_follow_mouse', False),
        'aim_toggle_key': getattr(config_instance, 'aim_toggle_key', 45),

        
        # ***** 新增的儲存項目 *****
        'model_path': getattr(config_instance, 'model_path', os.path.join('模型', 'Rivals.onnx')),
        'auto_fire_key2': getattr(config_instance, 'auto_fire_key2', 0x04),
        'AimToggle': getattr(config_instance, 'AimToggle', True),
        'show_fov': getattr(config_instance, 'show_fov', True),
        'show_boxes': getattr(config_instance, 'show_boxes', True),
        'show_status_panel': getattr(config_instance, 'show_status_panel', True), # ***** 新增此行 *****
        'single_target_mode': getattr(config_instance, 'single_target_mode', True), # ***** 新增：單目標模式 *****
        
        # 頭部和身體區域占比設定
        'head_width_ratio': getattr(config_instance, 'head_width_ratio', 0.38),
        'head_height_ratio': getattr(config_instance, 'head_height_ratio', 0.26),
        'body_width_ratio': getattr(config_instance, 'body_width_ratio', 0.87),
        
        # 優化：性能相關設置
        'performance_mode': getattr(config_instance, 'performance_mode', True),
        'max_queue_size': getattr(config_instance, 'max_queue_size', 1),
        
        # 新增：CPU性能優化參數
        'cpu_optimization': getattr(config_instance, 'cpu_optimization', True),
        'thread_priority': getattr(config_instance, 'thread_priority', "high"),
        'process_priority': getattr(config_instance, 'process_priority', "high"),
        'cpu_affinity': getattr(config_instance, 'cpu_affinity', None),
        
        # ***** 新增：音效提示系統 *****
        'enable_sound_alert': getattr(config_instance, 'enable_sound_alert', True),
        'sound_frequency': getattr(config_instance, 'sound_frequency', 1000),
        'sound_duration': getattr(config_instance, 'sound_duration', 100),
        'sound_interval': getattr(config_instance, 'sound_interval', 200),
        
        # 新增：高級/簡單模式切換
        'advanced_mode': getattr(config_instance, 'advanced_mode', True),
        
        # 新增：滑鼠移動方式
        'mouse_move_method': getattr(config_instance, 'mouse_move_method', 'delayed'),
    }
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("設定已儲存")
    except Exception as e:
        print(f"設定儲存失敗: {e}")
        
def load_config(config_instance):
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in data.items():
            # 為了兼容舊設定檔，檢查新參數是否存在
            if hasattr(config_instance, k):
                setattr(config_instance, k, v)
        print("設定檔已載入")
    except FileNotFoundError:
        print("未找到設定檔，使用預設值")
    except Exception as e:
        print(f"設定載入失敗: {e}")