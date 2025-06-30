# win_utils.py
import ctypes
import win32api
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

def is_key_pressed(key_code):
    return win32api.GetAsyncKeyState(key_code) & 0x8000 != 0