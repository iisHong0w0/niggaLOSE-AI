# settings_gui.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import win32api
import glob

# 從我們自己建立的模組中導入
from win_utils import VK_CODE_MAP
from config import save_config

class SettingsWindow:
    def __init__(self, master, config, start_ai_threads=None):
        self.master = master
        self.config = config
        self.start_ai_threads = start_ai_threads

        self.master.title("Axiom V3_h0pZ")
        self.master.geometry('888x888')
        self.master.protocol("WM_DELETE_WINDOW", self.quit_program)

        # --- 顏色與樣式 ---
        bg_main = "#250526"
        bg_frame = '#120606'
        fg_text = '#e0e6f0'
        accent = '#230622'
        btn_bg = '#230622'
        btn_active = '#330633'
        scale_trough = '#230622'
        scale_slider = '#330633'

        self.master.configure(bg=bg_main)

        # --- Logo ---
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'logo.png')
            # 設定視窗圖標
            tmp_ico = os.path.join(os.path.dirname(__file__), '_tmp_logo.ico')
            if not os.path.exists(tmp_ico):
                img = Image.open(icon_path)
                img.save(tmp_ico, format='ICO', sizes=[(32, 32)])
            self.master.iconbitmap(tmp_ico)
            # 顯示 Logo 圖片
            logo_img = Image.open(icon_path).resize((48, 48))
            self.logo_tk = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(self.master, image=self.logo_tk, bg=bg_main)
            logo_label.pack(side="top", pady=(10, 5))
        except Exception as e:
            print(f"Logo 載入失敗: {e}")

        tk.Label(self.master, text="Axiom V3", font=("Helvetica", 14, "bold"), bg=bg_main, fg=fg_text).pack(side="top", pady=(0, 10))

        # --- 主要內容區域 ---
        main_frame = tk.Frame(self.master, bg=bg_main)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- 區塊框架樣式函數 ---
        def create_section_frame(parent, title, width=None, height=None):
            frame = tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=bg_frame, fg=fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=10, pady=10)
            if width and height:
                frame.configure(width=width, height=height)
                frame.pack_propagate(False)
            return frame

        # --- 上方區域：模型設定 ---
        top_frame = create_section_frame(main_frame, "模型設定", 800, 80)
        top_frame.pack(fill="x", pady=(0, 10))
        
        model_inner_frame = tk.Frame(top_frame, bg=bg_frame)
        model_inner_frame.pack(fill="x", pady=5)
        
        tk.Label(model_inner_frame, text="模型:", bg=bg_frame, fg=fg_text, font=("Arial", 10)).pack(side="left", padx=(0, 10))
        
        # 模型選擇下拉選單
        model_dir = os.path.join(os.path.dirname(__file__), '模型')
        model_files = sorted([f for f in os.listdir(model_dir) if f.endswith('.onnx') or f.endswith('.pt')])
        self.model_var = tk.StringVar()
        default_model = 'Roblox通用.onnx' if 'Roblox通用.onnx' in model_files else (model_files[0] if model_files else '')
        self.model_var.set(default_model)
        self.config.model_path = os.path.join(model_dir, default_model)
        
        model_menu = ttk.Combobox(model_inner_frame, textvariable=self.model_var, values=model_files, 
                                 state="readonly", width=40, font=("Arial", 10))
        model_menu.pack(side="left", fill="x", expand=True)
        
        def on_model_change(event=None):
            selected = self.model_var.get()
            self.config.model_path = os.path.join(model_dir, selected)
            if self.start_ai_threads:
                ok = self.start_ai_threads(self.config.model_path)
                if ok:
                    print(f"已切換模型: {selected}")
                else:
                    print(f"模型載入失敗: {selected}")
        model_menu.bind("<<ComboboxSelected>>", on_model_change)
        
        # 啟動時自動載入預設模型
        if self.start_ai_threads:
            self.start_ai_threads(self.config.model_path)

        # --- 中間區域：三個主要區塊 ---
        middle_frame = tk.Frame(main_frame, bg=bg_main)
        middle_frame.pack(fill="both", expand=True)

        # 左側：參數調整
        left_frame = create_section_frame(middle_frame, "參數", 260, 400)
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        # 中間：程式控制
        center_frame = create_section_frame(middle_frame, "其他", 260, 400)
        center_frame.pack(side="left", fill="y", padx=5)

        # 右側：顯示選項
        right_frame = create_section_frame(middle_frame, "檢測", 260, 400)
        right_frame.pack(side="left", fill="y", padx=(10, 0))

        # --- 左側：參數調整區 ---
        # FOV大小
        fov_frame = tk.Frame(left_frame, bg=bg_frame)
        fov_frame.pack(fill="x", pady=5)
        self.fov_label = tk.Label(fov_frame, text=f"FOV大小: {self.config.fov_size}", bg=bg_frame, fg=fg_text)
        self.fov_label.pack(anchor="w")
        fov_scale = tk.Scale(fov_frame, from_=50, to=min(self.config.width, self.config.height), 
                            orient="horizontal", bg=bg_frame, fg=fg_text, troughcolor=scale_trough,
                            highlightbackground=accent, activebackground=scale_slider, length=220,
                            command=self.fov_size_configurator)
        fov_scale.set(self.config.fov_size)
        fov_scale.pack(fill="x", pady=2)
        

        # 概率閾值
        conf_frame = tk.Frame(left_frame, bg=bg_frame)
        conf_frame.pack(fill="x", pady=5)
        self.conf_label = tk.Label(conf_frame, text=f"檢測最低概率(%): {int(self.config.min_confidence * 100)}", bg=bg_frame, fg=fg_text)
        self.conf_label.pack(anchor="w")
        conf_scale = tk.Scale(conf_frame, from_=0, to=100, orient="horizontal", bg=bg_frame, fg=fg_text, 
                             troughcolor=scale_trough, highlightbackground=accent, activebackground=scale_slider, 
                             length=220, command=self.min_confidence_configurator)
        conf_scale.set(int(self.config.min_confidence * 100))
        conf_scale.pack(fill="x", pady=2)

        # 自動瞄準速度
        speed_frame = tk.Frame(left_frame, bg=bg_frame)
        speed_frame.pack(fill="x", pady=5)
        self.speed_label = tk.Label(speed_frame, text=f"自動瞄準速度: {int(self.config.aim_speed * 100)}", bg=bg_frame, fg=fg_text)
        self.speed_label.pack(anchor="w")
        speed_scale = tk.Scale(speed_frame, from_=1, to=100, orient="horizontal", bg=bg_frame, fg=fg_text,
                              troughcolor=scale_trough, highlightbackground=accent, activebackground=scale_slider,
                              length=220, command=self.aim_speed_configurator)
        speed_scale.set(int(self.config.aim_speed * 100))
        speed_scale.pack(fill="x", pady=2)

        # 檢測間隔
        interval_frame = tk.Frame(left_frame, bg=bg_frame)
        interval_frame.pack(fill="x", pady=5)
        self.interval_label = tk.Label(interval_frame, text=f"檢測間隔(ms): {int(self.config.detect_interval * 1000)}", bg=bg_frame, fg=fg_text)
        self.interval_label.pack(anchor="w")
        interval_scale = tk.Scale(interval_frame, from_=1, to=100, orient="horizontal", bg=bg_frame, fg=fg_text,
                                 troughcolor=scale_trough, highlightbackground=accent, activebackground=scale_slider,
                                 length=220, command=self.detect_interval_configurator)
        interval_scale.set(int(self.config.detect_interval * 1000))
        interval_scale.pack(fill="x", pady=2)

        # --- 中間：程式控制區 ---
        # 自動瞄準狀態
        self.AimLabel = tk.Label(center_frame, text=f"自動瞄準: {self.config.AimToggle}", bg=bg_frame, fg=fg_text, font=("Arial", 10))
        self.AimLabel.pack(pady=10)

        # 運算模式顯示
        provider_text = {"DmlExecutionProvider": "DirectML (GPU)", "CPUExecutionProvider": "CPU"}
        provider_str = provider_text.get(self.config.current_provider, self.config.current_provider)
        self.ProviderLabel = tk.Label(center_frame, text=f"運算模式: {provider_str}", bg=bg_frame, fg=fg_text, font=("Arial", 10))
        self.ProviderLabel.pack(pady=5)

        # 切換自動瞄準按鈕
        AimToggler = tk.Button(center_frame, text="自動瞄準開關", command=self.toggle_aim, 
                              bg=btn_bg, fg=fg_text, activebackground=btn_active, width=20, height=2)
        AimToggler.pack(pady=10)

        # 退出按鈕
        QuitButton = tk.Button(center_frame, text="退出並保存參數", command=self.quit_program, 
                              bg=btn_bg, fg=fg_text, activebackground=btn_active, width=20, height=2)
        QuitButton.pack(pady=10)

        # --- 右側：顯示選項區 ---
        # 顯示概率
        self.ConfidenceLabel = tk.Label(right_frame, text=f"顯示概率: {self.config.show_confidence}", bg=bg_frame, fg=fg_text, font=("Arial", 10))
        self.ConfidenceLabel.pack(pady=10)

        ToggleConfidenceButton = tk.Button(right_frame, text="顯示概率開關", command=self.toggle_show_confidence, 
                                          bg=btn_bg, fg=fg_text, activebackground=btn_active, width=18)
        ToggleConfidenceButton.pack(pady=5)

        # 勾選框區域
        checkbox_frame = tk.Frame(right_frame, bg=bg_frame)
        checkbox_frame.pack(pady=10, fill="x")

        # 保持檢測勾選框
        self.keep_detecting_var = tk.BooleanVar(value=getattr(self.config, 'keep_detecting', False))
        self.keep_detecting_checkbox = tk.Checkbutton(
            checkbox_frame, text="保持檢測", variable=self.keep_detecting_var, bg=bg_frame, fg=fg_text,
            selectcolor=bg_main, command=self.toggle_keep_detecting, font=("Arial", 9)
        )
        self.keep_detecting_checkbox.pack(anchor="w", pady=2)

        # FOV跟隨鼠標勾選框
        self.fov_follow_mouse_var = tk.BooleanVar(value=getattr(self.config, 'fov_follow_mouse', False))
        self.fov_follow_mouse_checkbox = tk.Checkbutton(
            checkbox_frame, text="FOV跟隨鼠標", variable=self.fov_follow_mouse_var, bg=bg_frame, fg=fg_text,
            selectcolor=bg_main, command=self.toggle_fov_follow_mouse, font=("Arial", 9)
        )
        self.fov_follow_mouse_checkbox.pack(anchor="w", pady=2)

        # --- 下方區域：按鍵及部位設定 ---
        bottom_frame = create_section_frame(main_frame, "按鍵及部位", 800, 120)
        bottom_frame.pack(fill="x", pady=(10, 0))

        # 按鍵設定區域與瞄準部位設定區域改用 grid 佈局
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        keys_frame = tk.Frame(bottom_frame, bg=bg_frame)
        keys_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=5)

        # 啟用瞄準按鍵
        tk.Label(keys_frame, text="瞄準按鍵 1:", bg=bg_frame, fg=fg_text, font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Label(keys_frame, text="瞄準按鍵 2:", bg=bg_frame, fg=fg_text, font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Label(keys_frame, text="自動開槍鍵:", bg=bg_frame, fg=fg_text, font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        tk.Label(keys_frame, text="自動瞄準開關鍵:", bg=bg_frame, fg=fg_text, font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=5, pady=2)

        self.listening_for_slot = None
        self.aimkey_btns = []
        
        for i in range(2):
            btn = tk.Button(keys_frame, text=self.get_key_name(self.config.AimKeys[i]), width=12,
                           command=lambda i=i: self.start_listening(i + 1), 
                           bg=btn_bg, fg=fg_text, activebackground=btn_active)
            btn.grid(row=i, column=1, padx=10, pady=2)
            self.aimkey_btns.append(btn)
        
        self.autofire_btn = tk.Button(keys_frame, text=self.get_key_name(self.config.auto_fire_key), width=12,
                                     command=lambda: self.start_listening(3), 
                                     bg=btn_bg, fg=fg_text, activebackground=btn_active)
        self.autofire_btn.grid(row=2, column=1, padx=10, pady=2)

        # 新增自動瞄準開關快捷鍵按鈕
        self.aimtogglekey_btn = tk.Button(keys_frame, text=self.get_key_name(getattr(self.config, 'aim_toggle_key', 0x2D)), width=12,
                                     command=lambda: self.start_listening(4), 
                                     bg=btn_bg, fg=fg_text, activebackground=btn_active)
        self.aimtogglekey_btn.grid(row=3, column=1, padx=10, pady=2)

        # 瞄準部位設定區域
        aim_frame = tk.Frame(bottom_frame, bg=bg_frame)
        aim_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=5)
        aim_frame.columnconfigure(0, weight=1)

        tk.Label(aim_frame, text="瞄準部位:", bg=bg_frame, fg=fg_text, font=("Arial", 10)).pack(pady=5)
        self.AimPartVar = tk.StringVar(value=self.config.aim_part)
        AimPartMenu = ttk.Combobox(aim_frame, textvariable=self.AimPartVar, values=["head", "body"], 
                                  state="readonly", width=10)
        AimPartMenu.pack(pady=5)
        AimPartMenu.bind("<<ComboboxSelected>>", self.aim_part_changed)

        # 開鏡延遲
        delay_frame = tk.Frame(aim_frame, bg=bg_frame)
        delay_frame.pack(pady=5)
        self.AutoFireDelayLabel = tk.Label(delay_frame, text=f"開鏡延遲: {self.config.auto_fire_delay:.2f}s", bg=bg_frame, fg=fg_text, font=("Arial", 9))
        self.AutoFireDelayLabel.pack()
        AutoFireDelaySlider = tk.Scale(delay_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, length=120,
                                      command=self.auto_fire_delay_configurator, bg=bg_frame, fg=fg_text, 
                                      troughcolor=scale_trough, highlightbackground=accent, activebackground=scale_slider)
        AutoFireDelaySlider.set(self.config.auto_fire_delay)
        AutoFireDelaySlider.pack()

        # 啟動按鍵監聽循環
        self.key_listener()
        # 啟動自動瞄準狀態同步輪詢
        self.poll_aimtoggle_status()

    # --- Class Methods (Callbacks) ---
    def quit_program(self):
        self.config.Running = False
        save_config(self.config)
        self.master.quit()
        self.master.destroy()

    def toggle_aim(self):
        self.config.AimToggle = not self.config.AimToggle
        self.AimLabel.config(text=f"自動瞄準: {self.config.AimToggle}")

    def fov_size_configurator(self, val):
        self.config.fov_size = int(val)
        self.fov_label.config(text=f"FOV大小: {int(val)}")

    def min_confidence_configurator(self, val):
        self.config.min_confidence = float(val) / 100.0
        self.conf_label.config(text=f"檢測最低概率(%): {int(val)}")
    
    def aim_speed_configurator(self, val):
        self.config.aim_speed = float(val) / 100.0
        self.speed_label.config(text=f"自動瞄準速度: {int(val)}")

    def detect_interval_configurator(self, val):
        self.config.detect_interval = int(val) / 1000.0
        self.interval_label.config(text=f"檢測間隔(ms): {int(val)}")

    def toggle_show_confidence(self):
        self.config.show_confidence = not self.config.show_confidence
        self.ConfidenceLabel.config(text=f"顯示概率: {self.config.show_confidence}")

    def auto_fire_delay_configurator(self, val):
        self.config.auto_fire_delay = float(val)
        self.AutoFireDelayLabel.config(text=f"開鏡延遲: {float(val):.2f}s")
        
    def get_key_name(self, key_code):
        return VK_CODE_MAP.get(key_code, f'0x{key_code:02X}')

    def start_listening(self, slot):
        self.listening_for_slot = slot
        if slot == 1 or slot == 2:
            self.aimkey_btns[slot-1].config(text='[按鍵...]')
        elif slot == 3:
            self.autofire_btn.config(text='[按鍵...]')
        elif slot == 4:
            self.aimtogglekey_btn.config(text='[按鍵...]')

    def key_listener(self):
        if self.listening_for_slot is not None:
            detected_key = None
            # 優先檢測滑鼠按鍵
            for key_code in [0x01, 0x02, 0x04, 0x05, 0x06]:
                if win32api.GetAsyncKeyState(key_code) & 0x8000:
                    detected_key = key_code
                    break
            # 否則檢測鍵盤按鍵
            if detected_key is None:
                for key_code in range(8, 256):
                    if win32api.GetAsyncKeyState(key_code) & 0x8000:
                        detected_key = key_code
                        break
            
            if detected_key:
                slot = self.listening_for_slot
                if slot == 1 or slot == 2:
                    self.config.AimKeys[slot-1] = detected_key
                    self.aimkey_btns[slot-1].config(text=self.get_key_name(detected_key))
                elif slot == 3:
                    self.config.auto_fire_key = detected_key
                    self.autofire_btn.config(text=self.get_key_name(detected_key))
                elif slot == 4:
                    self.config.aim_toggle_key = detected_key
                    self.aimtogglekey_btn.config(text=self.get_key_name(detected_key))
                self.listening_for_slot = None

        self.master.after(20, self.key_listener)

    def aim_part_changed(self, event=None):
        self.config.aim_part = self.AimPartVar.get()

    def toggle_keep_detecting(self):
        self.config.keep_detecting = self.keep_detecting_var.get()

    def toggle_fov_follow_mouse(self):
        self.config.fov_follow_mouse = self.fov_follow_mouse_var.get()

    def poll_aimtoggle_status(self):
        # 若 AimToggle 狀態與 GUI 顯示不同則自動更新
        current = self.config.AimToggle
        label_text = f"自動瞄準: {current}"
        if self.AimLabel.cget("text") != label_text:
            self.AimLabel.config(text=label_text)
        self.master.after(100, self.poll_aimtoggle_status)

def create_settings_gui(config, start_ai_threads=None):
    """主函式，用於從 main.py 啟動 GUI，支援模型切換"""
    root = tk.Tk()
    app = SettingsWindow(root, config, start_ai_threads)
    root.mainloop()