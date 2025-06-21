# config.py
import ctypes
import json
import os # <--- 新增導入 os 模組

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
        # 將預設路徑指向「模型」資料夾中的檔案
        default_model_name = 'Roblox通用.onnx' # 或者任何您希望的預設模型
        self.model_path = os.path.join('模型', default_model_name)
        self.current_provider = "CPUExecutionProvider" # 預設值，會被主程式更新

        # 瞄準與顯示設定
        self.AimKeys = [0x01, 0x02]  # 預設左鍵(0x01)與右鍵(0x02)
        self.fov_size = 666
        self.show_confidence = True
        self.min_confidence = 0.66
        self.aim_part = "head"
        self.aim_speed = 0.26
        self.detect_interval = 0.01
        self.aim_toggle_key = 0x2D  # 預設為 Insert 鍵 (0x2D)

        # 自動開槍
        self.auto_fire_key = 0x02
        self.auto_fire_delay = 0.26

        # 保持檢測功能
        self.keep_detecting = False
        # FOV 跟隨鼠標
        self.fov_follow_mouse = False

def save_config(config_instance):
    data = {
        'fov_size': config_instance.fov_size,
        'aim_speed': config_instance.aim_speed,
        'aim_part': config_instance.aim_part,
        'AimKeys': config_instance.AimKeys,
        'auto_fire_key': getattr(config_instance, 'auto_fire_key', 0x02),
        'auto_fire_delay': getattr(config_instance, 'auto_fire_delay', 1.0),
        'min_confidence': config_instance.min_confidence,
        'show_confidence': config_instance.show_confidence,
        'detect_interval': config_instance.detect_interval,
        'crosshairX': config_instance.crosshairX,
        'crosshairY': config_instance.crosshairY,
        'keep_detecting': getattr(config_instance, 'keep_detecting', False),
        'fov_follow_mouse': getattr(config_instance, 'fov_follow_mouse', False),
        'aim_toggle_key': getattr(config_instance, 'aim_toggle_key', 0x2D), # 0x2D 是 Insert 鍵
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
            setattr(config_instance, k, v)
        print("設定檔已載入")
    except FileNotFoundError:
        print("未找到設定檔，使用預設值")
    except Exception as e:
        print(f"設定載入失敗: {e}")