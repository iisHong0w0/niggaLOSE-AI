# win_utils.py
import ctypes
import win32api
import win32con
import time
import random
import threading
from language_manager import get_text

# Windows 虛擬按鍵碼對應英文名稱
VK_CODE_MAP = {
    0x01: "Mouse Left", 0x02: "Mouse Right", 0x04: "Mouse Middle", 0x05: "Mouse X1",
    0x06: "Mouse X2", 0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter",
    0x10: "Shift", 0x11: "Ctrl", 0x12: "Alt", 0x14: "CapsLock",
    0x1B: "Esc", 0x20: "Space", 0x25: "Left", 0x26: "Up", 0x27: "Right",
    0x28: "Down", 0x2C: "PrintScreen", 0x2D: "Insert", 0x2E: "Delete",
    0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4", 0x35: "5",
    0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9", 0x41: "A", 0x42: "B",
    0x43: "C", 0x44: "D", 0x45: "E", 0x46: "F", 0x47: "G", 0x48: "H",
    0x49: "I", 0x4A: "J", 0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N",
    0x4F: "O", 0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S", 0x54: "T",
    0x55: "U", 0x56: "V", 0x57: "W", 0x58: "X", 0x59: "Y", 0x5A: "Z",
    0x5B: "Win", 0x60: "Num0", 0x61: "Num1", 0x62: "Num2", 0x63: "Num3",
    0x64: "Num4", 0x65: "Num5", 0x66: "Num6", 0x67: "Num7", 0x68: "Num8",
    0x69: "Num9", 0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8", 0x78: "F9",
    0x79: "F10", 0x7A: "F11", 0x7B: "F12", 0x90: "NumLock", 0x91: "ScrollLock",
    0xA0: "Shift(L)", 0xA1: "Shift(R)", 0xA2: "Ctrl(L)", 0xA3: "Ctrl(R)",
    0xA4: "Alt(L)", 0xA5: "Alt(R)",
}

# 按鍵名稱多語言對應表
VK_TRANSLATIONS = {
    "zh_tw": {
        "Mouse Left": "滑鼠左鍵", "Mouse Right": "滑鼠右鍵", "Mouse Middle": "滑鼠中鍵", "Mouse X1": "滑鼠側鍵1",
        "Mouse X2": "滑鼠側鍵2", "Backspace": "Backspace", "Tab": "Tab", "Enter": "Enter",
        "Shift": "Shift", "Ctrl": "Ctrl", "Alt": "Alt", "CapsLock": "CapsLock",
        "Esc": "Esc", "Space": "Space", "Left": "←", "Up": "↑", "Right": "→",
        "Down": "↓", "PrintScreen": "PrintScreen", "Insert": "Insert", "Delete": "Delete",
        "Num0": "數字鍵0", "Num1": "數字鍵1", "Num2": "數字鍵2", "Num3": "數字鍵3", "Num4": "數字鍵4",
        "Num5": "數字鍵5", "Num6": "數字鍵6", "Num7": "數字鍵7", "Num8": "數字鍵8", "Num9": "數字鍵9",
        "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5", "F6": "F6", "F7": "F7", "F8": "F8", "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
        "Win": "Win", "Shift(L)": "Shift(左)", "Shift(R)": "Shift(右)", "Ctrl(L)": "Ctrl(左)", "Ctrl(R)": "Ctrl(右)", "Alt(L)": "Alt(左)", "Alt(R)": "Alt(右)"
    },
    "en": {}  # 英文直接顯示原名
}

def get_vk_name(key_code):
    name = VK_CODE_MAP.get(key_code, f'0x{key_code:02X}')
    lang = None
    try:
        from language_manager import language_manager
        lang = language_manager.get_current_language()
    except Exception:
        lang = "zh_tw"
    if lang != "en":
        return VK_TRANSLATIONS.get(lang, {}).get(name, name)
    return name

# ===== 高級反檢測滑鼠移動方式 =====

# 全局變量用於緩存
_last_move_time = 0
_move_accumulator_x = 0.0
_move_accumulator_y = 0.0
_move_lock = threading.Lock()

# 方式1: 原始 SendInput (容易被檢測)
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

def send_mouse_move_sendinput(dx, dy):
    """方式1: SendInput API (原始方式，容易被檢測)"""
    extra = ctypes.c_ulong(0)
    ii_ = INPUT._INPUT_UNION()
    ii_.mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    command = INPUT(INPUT_MOUSE, ii_)
    ctypes.windll.user32.SendInput(1, ctypes.byref(command), ctypes.sizeof(command))

# 方式2: SetCursorPos (較隱蔽)
def send_mouse_move_setcursor(dx, dy):
    """方式2: SetCursorPos 絕對位置移動"""
    try:
        current_x, current_y = win32api.GetCursorPos()
        new_x = current_x + dx
        new_y = current_y + dy
        win32api.SetCursorPos((new_x, new_y))
    except Exception as e:
        print(f"SetCursorPos 移動失敗: {e}")

# 方式3: 分段移動 (模擬人類移動) - 修復版本
def send_mouse_move_smooth(dx, dy, steps=2):
    """方式3: 分段平滑移動，模擬人類移動軌跡 - 減少延遲"""
    try:
        current_x, current_y = win32api.GetCursorPos()
        
        # 減少步數和延遲以提高響應速度
        step_x = dx / steps
        step_y = dy / steps
        
        for i in range(steps):
            # 減少隨機偏移量
            random_offset_x = random.uniform(-0.2, 0.2)
            random_offset_y = random.uniform(-0.2, 0.2)
            
            move_x = step_x + random_offset_x
            move_y = step_y + random_offset_y
            
            current_x += move_x
            current_y += move_y
            
            win32api.SetCursorPos((int(current_x), int(current_y)))
            
            # 大幅減少延遲
            if i < steps - 1:  # 最後一步不延遲
                time.sleep(random.uniform(0.0005, 0.001))
            
    except Exception as e:
        print(f"平滑移動失敗: {e}")

# 方式4: 硬件層級模擬
def send_mouse_move_hardware(dx, dy):
    """方式4: 硬件層級滑鼠移動模擬"""
    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
    except Exception as e:
        print(f"硬件層級移動失敗: {e}")

# 方式5: 累積移動 (反檢測) - 新增
def send_mouse_move_accumulate(dx, dy):
    """方式5: 累積移動 - 避免頻繁小幅移動被檢測"""
    global _last_move_time, _move_accumulator_x, _move_accumulator_y
    
    with _move_lock:
        current_time = time.time()
        
        # 累積移動量
        _move_accumulator_x += dx
        _move_accumulator_y += dy
        
        # 只有當累積量足夠大或時間間隔足夠長時才執行移動
        if (abs(_move_accumulator_x) >= 3 or abs(_move_accumulator_y) >= 3 or 
            current_time - _last_move_time > 0.01):
            
            try:
                # 使用隨機的API
                if random.choice([True, False]):
                    win32api.SetCursorPos((
                        win32api.GetCursorPos()[0] + int(_move_accumulator_x),
                        win32api.GetCursorPos()[1] + int(_move_accumulator_y)
                    ))
                else:
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 
                                       int(_move_accumulator_x), 
                                       int(_move_accumulator_y), 0, 0)
                
                _move_accumulator_x = 0
                _move_accumulator_y = 0
                _last_move_time = current_time
                
            except Exception as e:
                print(f"累積移動失敗: {e}")

# 方式6: 延遲執行 (異步) - 新增
def send_mouse_move_delayed(dx, dy):
    """方式6: 延遲執行移動（僅用mouse_event，無隨機延遲/隨機API）"""
    def delayed_move():
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        except Exception:
            pass
    
    # 異步執行
    threading.Thread(target=delayed_move, daemon=True).start()

# 方式7: 混合API調用 - 新增
def send_mouse_move_mixed(dx, dy):
    """方式7: 混合多種API調用方式"""
    try:
        # 隨機選擇實現方式
        method = random.randint(1, 4)
        
        if method == 1:
            # SetCursorPos
            current_x, current_y = win32api.GetCursorPos()
            win32api.SetCursorPos((current_x + dx, current_y + dy))
        elif method == 2:
            # mouse_event
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        elif method == 3:
            # 分兩步移動
            half_dx, half_dy = dx // 2, dy // 2
            current_x, current_y = win32api.GetCursorPos()
            win32api.SetCursorPos((current_x + half_dx, current_y + half_dy))
            time.sleep(0.0001)
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx - half_dx, dy - half_dy, 0, 0)
        else:
            # SendInput 但添加隨機時間戳
            extra = ctypes.c_ulong(random.randint(1000, 9999))
            ii_ = INPUT._INPUT_UNION()
            ii_.mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
            command = INPUT(INPUT_MOUSE, ii_)
            ctypes.windll.user32.SendInput(1, ctypes.byref(command), ctypes.sizeof(command))
            
    except Exception as e:
        print(f"混合移動失敗: {e}")

# 方式8: 貝塞爾曲線移動 (修復版本)
def send_mouse_move_bezier(dx, dy, steps=3):
    """方式8: 貝塞爾曲線移動 - 減少延遲版本"""
    try:
        current_x, current_y = win32api.GetCursorPos()
        target_x = current_x + dx
        target_y = current_y + dy
        
        # 簡化控制點計算
        control_x = current_x + dx * 0.5 + random.uniform(-abs(dx)*0.1, abs(dx)*0.1)
        control_y = current_y + dy * 0.5 + random.uniform(-abs(dy)*0.1, abs(dy)*0.1)
        
        # 減少步數
        for i in range(steps + 1):
            t = i / steps
            
            # 二次貝塞爾曲線公式
            x = (1-t)**2 * current_x + 2*(1-t)*t * control_x + t**2 * target_x
            y = (1-t)**2 * current_y + 2*(1-t)*t * control_y + t**2 * target_y
            
            win32api.SetCursorPos((int(x), int(y)))
            
            # 大幅減少延遲
            if i < steps:
                time.sleep(0.0005)
            
    except Exception as e:
        print(f"貝塞爾移動失敗: {e}")

# 方式9: 隨機選擇 (更新版本)
def send_mouse_move_random(dx, dy):
    """方式9: 隨機選擇移動方式，增加不可預測性"""
    methods = [
        send_mouse_move_setcursor,
        send_mouse_move_hardware,
        send_mouse_move_accumulate,
        send_mouse_move_mixed,
        lambda x, y: send_mouse_move_smooth(x, y, 2),
    ]
    
    # 隨機選擇移動方式
    method = random.choice(methods)
    method(dx, dy)

# 主要滑鼠移動函數 - 更新版本
def send_mouse_move(dx, dy, method="mixed"):
    """
    主要滑鼠移動函數
    method 選項:
    - "sendinput": 原始SendInput (最快但容易被檢測)
    - "setcursor": SetCursorPos (較隱蔽)
    - "smooth": 平滑移動 (模擬人類)
    - "hardware": 硬件層級 (較隱蔽)
    - "accumulate": 累積移動 (反檢測)
    - "delayed": 延遲執行 (異步)
    - "mixed": 混合API (推薦)
    - "bezier": 貝塞爾曲線 (最像人類)
    - "random": 隨機方式 (不可預測)
    """
    if abs(dx) < 1 and abs(dy) < 1:
        return  # 移動量太小，跳過
    
    if method == "sendinput":
        send_mouse_move_sendinput(dx, dy)
    elif method == "setcursor":
        send_mouse_move_setcursor(dx, dy)
    elif method == "smooth":
        send_mouse_move_smooth(dx, dy)
    elif method == "hardware":
        send_mouse_move_hardware(dx, dy)
    elif method == "accumulate":
        send_mouse_move_accumulate(dx, dy)
    elif method == "delayed":
        send_mouse_move_delayed(dx, dy)
    elif method == "mixed":
        send_mouse_move_mixed(dx, dy)
    elif method == "bezier":
        send_mouse_move_bezier(dx, dy)
    elif method == "random":
        send_mouse_move_random(dx, dy)
    else:
        # 默認使用混合方式
        send_mouse_move_mixed(dx, dy)

def is_key_pressed(key_code):
    return win32api.GetAsyncKeyState(key_code) & 0x8000 != 0