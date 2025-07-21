# settings_gui.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import win32api
import glob
import math
from typing import Union
import tkinter.messagebox as messagebox

# 從我們自己建立的模組中導入
from win_utils import VK_CODE_MAP, get_vk_name
from config import save_config
from language_manager import language_manager, get_text  # 新增導入
from about import show_about_window  # 導入關於視窗
from preset_manager import PresetManagerGUI  # ***** 新增：導入預設管理器 *****

# PIL 兼容性處理
try:
    LANCZOS_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS_FILTER = Image.LANCZOS  # type: ignore

class HeartButton(tk.Canvas):
    """心型按鈕自定義組件"""
    def __init__(self, parent, text="", command=None, bg="#FF0000", fg="white", width=120, height=50, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.bg_color = bg
        self.fg_color = fg
        self.width = width
        self.height = height
        
        # 綁定點擊事件
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self.draw_heart()
    
    def draw_heart(self, hover=False):
        """繪製心型"""
        self.delete("all")
        
        # 計算心型的中心點
        center_x = self.width // 2
        center_y = self.height // 2 - 2
        
        # 心型座標點
        points = []
        scale = min(self.width, self.height) * 0.018  # 調整大小使其更大一點
        
        # 使用心型的數學公式生成點
        for i in range(360):
            t = math.radians(i)
            # 心型公式: x = 16sin³(t), y = 13cos(t) - 5cos(2t) - 2cos(3t) - cos(4t)
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            
            # 縮放和移動到中心
            x = center_x + x * scale
            y = center_y + y * scale
            
            points.extend([x, y])
        
        # 選擇顏色（懸停時稍微變亮）
        fill_color = "#FF6666" if hover else self.bg_color
        outline_color = "#FF8888" if hover else "#CC0000"
        
        # 繪製心型
        self.create_polygon(points, fill=fill_color, outline=outline_color, width=2, smooth=True)
        
        # 繪製文字
        text_color = "white" if not hover else "#FFEEEE"
        self.create_text(center_x, center_y + 2, text=self.text, fill=text_color, 
                        font=("Arial", 10, "bold"), anchor="center")
    
    def _on_click(self, event):
        """處理點擊事件"""
        if self.command:
            self.command()
    
    def _on_enter(self, event):
        """滑鼠進入"""
        self.draw_heart(hover=True)
    
    def _on_leave(self, event):
        """滑鼠離開"""
        self.draw_heart(hover=False)
    
    def config(self, **kwargs):
        """配置按鈕屬性"""
        if 'text' in kwargs:
            self.text = kwargs['text']
            self.draw_heart()

class SettingsWindow:
    def __init__(self, master, config, start_ai_threads=None):
        self.master = master
        self.config = config
        self.start_ai_threads = start_ai_threads
        self.language_manager = language_manager  # 新增
        self.master.title(get_text("window_title"))
        self.master.geometry('999x777')
        self.master.protocol("WM_DELETE_WINDOW", self.quit_program)

        # --- 顏色與樣式 (設定為實例屬性) ---
        self.bg_main = "#250526"
        self.bg_frame = '#120606'
        self.fg_text = '#e0e6f0'
        self.accent = '#230621'
        self.btn_bg = '#230621'
        self.btn_active = '#250526'
        self.scale_trough = '#250526'
        self.scale_slider = '#120606'

        self.master.configure(bg=self.bg_main)

        # --- 標題列：logo+標題致中 ---
        title_bar = tk.Frame(self.master, bg=self.bg_main)
        title_bar.pack(fill="x", pady=(10, 10))
        center_frame = tk.Frame(title_bar, bg=self.bg_main)
        center_frame.pack(expand=True, fill="x")
        # 設定視窗icon為logo.ico
        icon_path = os.path.join(os.path.dirname(__file__), 'logo.ico')
        self.master.iconbitmap(icon_path)
        # 標題列顯示logo.png
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        logo_img = Image.open(logo_path)
        logo_img = logo_img.resize((64, 64), LANCZOS_FILTER)
        self.logo_photo = ImageTk.PhotoImage(logo_img)
        tk.Label(center_frame, image=self.logo_photo, bg=self.bg_main).pack(side="left", padx=(0, 16))
        tk.Label(center_frame, text="Axiom V4", font=("Helvetica", 22, "bold"), bg=self.bg_main, fg=self.fg_text).pack(side="left")
        
        # --- 捐款按鈕與語言切換按鈕 ---
        lang_frame = tk.Frame(center_frame, bg=self.bg_main)
        lang_frame.pack(side="right", padx=20)
        
        # 根據當前語言決定按鈕文字
        current_lang = self.language_manager.get_current_language()
        donate_text = get_text("donate") if current_lang == "zh_tw" else get_text("donate_en")
        button_text = get_text("english") if current_lang == "zh_tw" else get_text("chinese")
        
        # 心型捐款按鈕
        self.donate_button = HeartButton(lang_frame,
                                        text=donate_text,
                                        command=self.open_donate_page,
                                        bg="#FF0000",
                                        width=140,
                                        height=65)
        self.donate_button.configure(bg=self.bg_main)  # 設置 Canvas 背景與窗口背景一致
        self.donate_button.pack(side="right", pady=5, padx=(0, 8))

        # 語言切換按鈕
        self.lang_button = tk.Button(lang_frame, 
                                    text=button_text, # 使用動態文字
                                    command=self.toggle_language,
                                    bg="#FF0000",
                                    fg='white',
                                    font=("Arial", 10, "bold"),
                                    activebackground="#0026FF",
                                    relief="raised",
                                    bd=2,
                                    width=12)
        self.lang_button.pack(side="right", pady=5, padx=(0, 8))
        
        # 模式切換按鈕
        mode_text = get_text("simple_mode") if getattr(self.config, 'advanced_mode', True) else get_text("advanced_mode")
        self.mode_button = tk.Button(lang_frame, 
                                    text=mode_text,
                                    command=self.toggle_mode,
                                    bg="#0066FF",
                                    fg='white',
                                    font=("Arial", 10, "bold"),
                                    activebackground="#0088FF",
                                    relief="raised",
                                    bd=2,
                                    width=12)
        self.mode_button.pack(side="right", pady=5)
        # ------

        # --- 主要內容區域 ---
        main_frame = tk.Frame(self.master, bg=self.bg_main)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- 區塊框架樣式函數 ---
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)

        # --- 創建分頁式界面 ---
        # 配置分頁樣式
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=self.bg_main, borderwidth=0)
        style.configure("TNotebook.Tab", 
                       background=self.accent, 
                       foreground=self.fg_text, 
                       padding=[12, 8], 
                       borderwidth=1,
                       focuscolor='none')
        style.map("TNotebook.Tab", 
                 background=[("selected", self.btn_bg), ("active", self.btn_active)],
                 foreground=[("selected", self.fg_text), ("active", self.fg_text)])

        # 主分頁容器
        self.main_notebook = ttk.Notebook(main_frame)
        self.main_notebook.pack(fill="both", expand=True, pady=10)

        # 建立各個分頁
        self.create_basic_settings_tab(self.main_notebook)
        self.create_aim_control_tab(self.main_notebook)
        self.create_keys_settings_tab(self.main_notebook)
        self.create_auto_features_tab(self.main_notebook)
        self.create_display_options_tab(self.main_notebook)
        self.create_preset_management_tab(self.main_notebook)  # ***** 新增：預設管理分頁 *****
        self.create_program_control_tab(self.main_notebook)
        
        # 初始化模式相關變數
        self.preset_management_tab_index = 5  # 預設管理分頁的索引
        self.update_mode_visibility()

        self.listening_for_slot = None
        self.key_listener()
        self.poll_aimtoggle_status()

        
        # 初始化模型
        if self.start_ai_threads: 
            self.start_ai_threads(self.config.model_path)
            # 延遲一下等待模型加載完成後更新狀態標籤
            self.master.after(1000, self.update_status_labels)

    def create_basic_settings_tab(self, notebook):
        """建立基本設定分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_basic"))
        
        # 區塊框架樣式函數
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        # 模型設定
        model_frame = create_section_frame(tab, get_text("model_settings"))
        model_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(model_frame, text=get_text("model"), bg=self.bg_frame, fg=self.fg_text, font=("Arial", 10)).pack(side="left", padx=(0, 10))
        
        # 修正模型資料夾路徑
        model_dir = os.path.join(os.path.dirname(__file__), '模型')
        if not os.path.exists(model_dir):
            model_dir = '模型'  # 向後兼容
        model_files = sorted([f for f in os.listdir(model_dir) if f.endswith('.onnx') or f.endswith('.pt')])
        self.model_var = tk.StringVar(value=os.path.basename(self.config.model_path))
        
        model_menu = ttk.Combobox(model_frame, textvariable=self.model_var, values=model_files, 
                                 state="readonly", width=40, font=("Arial", 10))
        model_menu.pack(side="left", fill="x", expand=True)
        model_menu.bind("<<ComboboxSelected>>", self.on_model_change)
        
        # 基本參數
        params_frame = create_section_frame(tab, get_text("general_params"))
        params_frame.pack(fill="x", pady=(0, 15))
        
        self.fov_size_slider = self.create_slider(params_frame, get_text("fov_size"), self.config.fov_size, 50, min(self.config.width, self.config.height), self.fov_size_configurator, slider_name="fov_size")
        self.min_confidence_slider = self.create_slider(params_frame, get_text("min_confidence"), self.config.min_confidence * 100, 0, 100, self.min_confidence_configurator, slider_name="min_confidence")
        self.detect_interval_slider = self.create_slider(params_frame, get_text("detect_interval"), self.config.detect_interval * 1000, 0.1, 10, self.detect_interval_configurator, slider_name="detect_interval")
        
        # ***** 新增：單目標模式設定 *****
        self.single_target_var = tk.BooleanVar(value=getattr(self.config, 'single_target_mode', True))
        single_target_checkbox = tk.Checkbutton(params_frame, 
                                               text=get_text("single_target_mode"), 
                                               variable=self.single_target_var, 
                                               command=self.toggle_single_target_mode, 
                                               bg=self.bg_frame, 
                                               fg=self.fg_text, 
                                               selectcolor=self.bg_main, 
                                               font=("Arial", 10))
        single_target_checkbox.pack(anchor="w", pady=(5, 0))
        # 移除 CPU 性能優化區塊

    def create_aim_control_tab(self, notebook):
        """建立瞄準控制分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_aim_control"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        # 檢查是否為高級模式
        is_advanced = getattr(self.config, 'advanced_mode', True)
        
        # PID 控制器
        pid_frame = create_section_frame(tab, get_text("aim_speed_pid"))
        pid_frame.pack(fill="x", pady=(0, 15))

        if is_advanced:
            # 高級模式：分離X/Y軸控制，顯示完整PID參數
            pid_tabs = ttk.Notebook(pid_frame)
            style = ttk.Style()
            style.configure("PID.TNotebook", background=self.bg_frame, borderwidth=0)
            style.configure("PID.TNotebook.Tab", 
                           background=self.accent, 
                           foreground=self.fg_text, 
                           padding=[8, 4], 
                           borderwidth=1)
            
            tab_x = tk.Frame(pid_tabs, bg=self.bg_frame, padx=5, pady=5)
            tab_y = tk.Frame(pid_tabs, bg=self.bg_frame, padx=5, pady=5)
            pid_tabs.add(tab_x, text=get_text("horizontal_x"))
            pid_tabs.add(tab_y, text=get_text("vertical_y"))
            pid_tabs.pack(expand=True, fill="both")
            
            self.pid_kp_x_slider = self.create_slider(tab_x, get_text("reaction_speed_p"), self.config.pid_kp_x, 0, 1, self.pid_kp_x_configurator, res=0.001, val_format=".3f", length=400, slider_name="pid_kp_x")
            self.pid_ki_x_slider = self.create_slider(tab_x, get_text("error_correction_i"), self.config.pid_ki_x, 0, 0.1, self.pid_ki_x_configurator, res=0.001, val_format=".3f", length=400, slider_name="pid_ki_x")
            self.pid_kd_x_slider = self.create_slider(tab_x, get_text("stability_suppression_d"), self.config.pid_kd_x, 0, 0.2, self.pid_kd_x_configurator, res=0.001, val_format=".3f", length=400, slider_name="pid_kd_x")

            self.pid_kp_y_slider = self.create_slider(tab_y, get_text("reaction_speed_p"), self.config.pid_kp_y, 0, 1, self.pid_kp_y_configurator, res=0.001, val_format=".3f", length=400, slider_name="pid_kp_y")
            self.pid_ki_y_slider = self.create_slider(tab_y, get_text("error_correction_i"), self.config.pid_ki_y, 0, 0.1, self.pid_ki_y_configurator, res=0.001, val_format=".3f", length=400, slider_name="pid_ki_y")
            self.pid_kd_y_slider = self.create_slider(tab_y, get_text("stability_suppression_d"), self.config.pid_kd_y, 0, 0.2, self.pid_kd_y_configurator, res=0.001, val_format=".3f", length=400, slider_name="pid_kd_y")
        else:
            # 簡單模式：統一X/Y軸速度，只顯示P值
            self.unified_pid_kp_slider = self.create_slider(pid_frame, get_text("unified_xy_speed"), self.config.pid_kp_x, 0, 1, self.unified_pid_kp_configurator, res=0.001, val_format=".3f", length=400, slider_name="unified_pid_kp")
            
            # 保留原有的滑條變數以保持兼容性，但隱藏
            self.pid_kp_x_slider = None
            self.pid_ki_x_slider = None
            self.pid_kd_x_slider = None
            self.pid_kp_y_slider = None
            self.pid_ki_y_slider = None
            self.pid_kd_y_slider = None

        # 瞄準部位設定
        aim_frame = create_section_frame(tab, get_text("aim_part"))
        aim_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(aim_frame, text=get_text("aim_part"), bg=self.bg_frame, fg=self.fg_text).pack(anchor="w", pady=(0, 5))
        
        # 將內部英文值轉換為顯示的中文值
        display_aim_part = self.config.aim_part
        if self.config.aim_part == "head":
            display_aim_part = get_text("head")
        elif self.config.aim_part == "body":
            display_aim_part = get_text("body")
        elif self.config.aim_part == "頭部":  # 向後兼容舊的中文值
            display_aim_part = get_text("head")
            self.config.aim_part = "head"
        elif self.config.aim_part == "身體":  # 向後兼容舊的中文值
            display_aim_part = get_text("body")
            self.config.aim_part = "body"
        
        self.AimPartVar = tk.StringVar(value=display_aim_part)
        ttk.Combobox(aim_frame, textvariable=self.AimPartVar, values=[get_text("head"), get_text("body")], state="readonly", width=15).pack(anchor="w", pady=(0,10))
        self.AimPartVar.trace_add("write", self.aim_part_changed)
        
        # 目標區域設定 - 在簡單模式下隱藏
        if is_advanced:
            area_frame = create_section_frame(tab, get_text("target_area_settings"))
            area_frame.pack(fill="x")
            
            area_left = tk.Frame(area_frame, bg=self.bg_frame)
            area_right = tk.Frame(area_frame, bg=self.bg_frame)
            area_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
            area_right.pack(side="right", fill="both", expand=True)
            
            # 頭部設定
            tk.Label(area_left, text="頭部區域:", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.head_width_ratio_slider = self.create_slider(area_left, get_text("head_width_ratio"), self.config.head_width_ratio * 100, 10, 100, self.head_width_ratio_configurator, res=1, val_format=".0f")
            self.head_height_ratio_slider = self.create_slider(area_left, get_text("head_height_ratio"), self.config.head_height_ratio * 100, 10, 50, self.head_height_ratio_configurator, res=1, val_format=".0f")
            
            # 身體設定
            tk.Label(area_right, text="身體區域:", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
            self.body_width_ratio_slider = self.create_slider(area_right, get_text("body_width_ratio"), self.config.body_width_ratio * 100, 50, 100, self.body_width_ratio_configurator, res=1, val_format=".0f")
            
            # 添加說明文字
            tk.Label(area_right, text="※ 身體高度 = 100% - 頭部高度", bg=self.bg_frame, fg="#888888", font=("Arial", 8)).pack(anchor="w", pady=(5, 0))
        else:
            # 簡單模式下隱藏頭身比例設定，設置為None以保持兼容性
            self.head_width_ratio_slider = None
            self.head_height_ratio_slider = None
            self.body_width_ratio_slider = None

    def create_keys_settings_tab(self, notebook):
        """建立按鍵設定分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_keys"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        keys_frame = create_section_frame(tab, get_text("keys_and_auto_fire"))
        keys_frame.pack(fill="both", expand=True)
        
        self.key_buttons = {}
        key_map = {
            "aim1": {"text": get_text("aim_key_1"), "slot": 1}, 
            "aim2": {"text": get_text("aim_key_2"), "slot": 2},
            "aim3": {"text": get_text("aim_key_3"), "slot": 6},  # 新增第三個瞄準按鍵
            "autofire": {"text": get_text("auto_fire_key_1"), "slot": 3}, 
            "autofire2": {"text": get_text("auto_fire_key_2"), "slot": 5},
            "toggle": {"text": get_text("toggle_key"), "slot": 4}
        }
        
        for i, (key, val) in enumerate(key_map.items()):
            tk.Label(keys_frame, text=val["text"], bg=self.bg_frame, fg=self.fg_text, font=("Arial", 10)).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 10))
            btn = tk.Button(keys_frame, text="...", width=15, command=lambda s=val["slot"]: self.start_listening(s), 
                           bg=self.btn_bg, fg=self.fg_text, activebackground=self.btn_active, font=("Arial", 9))
            btn.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.key_buttons[val["slot"]] = btn
        
        self.update_key_buttons()

    def create_auto_features_tab(self, notebook):
        """建立自動功能分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_auto_features"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        # 自動開火設定
        autofire_frame = create_section_frame(tab, get_text("auto_fire_key_1"))
        autofire_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(autofire_frame, text=get_text("auto_fire_target"), bg=self.bg_frame, fg=self.fg_text).pack(anchor="w", pady=(0, 5))
        
        # 將內部英文值轉換為顯示的中文值
        display_autofire_part = self.config.auto_fire_target_part
        if self.config.auto_fire_target_part == "head":
            display_autofire_part = get_text("head")
        elif self.config.auto_fire_target_part == "body":
            display_autofire_part = get_text("body")
        elif self.config.auto_fire_target_part == "both":
            display_autofire_part = get_text("both")
        elif self.config.auto_fire_target_part == "頭部":  # 向後兼容舊的中文值
            display_autofire_part = get_text("head")
            self.config.auto_fire_target_part = "head"
        elif self.config.auto_fire_target_part == "身體":  # 向後兼容舊的中文值
            display_autofire_part = get_text("body")
            self.config.auto_fire_target_part = "body"
        elif self.config.auto_fire_target_part == "兩者":  # 向後兼容舊的中文值
            display_autofire_part = get_text("both")
            self.config.auto_fire_target_part = "both"
        
        self.AutoFirePartVar = tk.StringVar(value=display_autofire_part)
        ttk.Combobox(autofire_frame, textvariable=self.AutoFirePartVar, values=[get_text("head"), get_text("body"), get_text("both")], state="readonly", width=15).pack(anchor="w", pady=(0,10))
        self.AutoFirePartVar.trace_add("write", self.auto_fire_part_changed)

        self.auto_fire_delay_slider = self.create_slider(autofire_frame, get_text("scope_delay"), self.config.auto_fire_delay, 0, 1, self.auto_fire_delay_configurator, res=0.01, val_format=".2f")
        self.auto_fire_interval_slider = self.create_slider(autofire_frame, get_text("fire_interval"), self.config.auto_fire_interval, 0, 1, self.auto_fire_interval_configurator, res=0.01, val_format=".2f")
        


    def create_display_options_tab(self, notebook):
        """建立顯示選項分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_display"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        options_frame = create_section_frame(tab, get_text("function_options"))
        options_frame.pack(fill="x")
        
        self.show_confidence_var = tk.BooleanVar(value=self.config.show_confidence)
        tk.Checkbutton(options_frame, text=get_text("show_confidence"), variable=self.show_confidence_var, command=self.toggle_show_confidence, bg=self.bg_frame, fg=self.fg_text, selectcolor=self.bg_main, font=("Arial", 10)).pack(anchor="w", pady=5)

        self.show_fov_var = tk.BooleanVar(value=getattr(self.config, 'show_fov', True))
        tk.Checkbutton(options_frame, text=get_text("show_fov"), variable=self.show_fov_var, command=self.toggle_show_fov, bg=self.bg_frame, fg=self.fg_text, selectcolor=self.bg_main, font=("Arial", 10)).pack(anchor="w", pady=5)

        self.show_boxes_var = tk.BooleanVar(value=getattr(self.config, 'show_boxes', True))
        tk.Checkbutton(options_frame, text=get_text("show_boxes"), variable=self.show_boxes_var, command=self.toggle_show_boxes, bg=self.bg_frame, fg=self.fg_text, selectcolor=self.bg_main, font=("Arial", 10)).pack(anchor="w", pady=5)

        self.keep_detecting_var = tk.BooleanVar(value=self.config.keep_detecting)
        tk.Checkbutton(options_frame, text=get_text("keep_detecting"), variable=self.keep_detecting_var, command=self.toggle_keep_detecting, bg=self.bg_frame, fg=self.fg_text, selectcolor=self.bg_main, font=("Arial", 10)).pack(anchor="w", pady=5)

        self.fov_follow_mouse_var = tk.BooleanVar(value=self.config.fov_follow_mouse)
        self.fov_follow_mouse_checkbox = tk.Checkbutton(options_frame, text=get_text("fov_follow_mouse"), variable=self.fov_follow_mouse_var, command=self.toggle_fov_follow_mouse, bg=self.bg_frame, fg=self.fg_text, selectcolor=self.bg_main, font=("Arial", 10))
        self.fov_follow_mouse_checkbox.pack(anchor="w", pady=5)

        # ***** 新增：音效提示系統設定 - 只在高級模式下顯示 *****
        is_advanced = getattr(self.config, 'advanced_mode', True)
        if is_advanced:
            sound_frame = create_section_frame(tab, get_text("sound_alert_system"))
            sound_frame.pack(fill="x", pady=(15, 0))
            
            # 啟用音效提示復選框
            self.enable_sound_alert_var = tk.BooleanVar(value=getattr(self.config, 'enable_sound_alert', True))
            tk.Checkbutton(sound_frame, 
                          text=get_text("enable_sound_alert"), 
                          variable=self.enable_sound_alert_var, 
                          command=self.toggle_sound_alert, 
                          bg=self.bg_frame, 
                          fg=self.fg_text, 
                          selectcolor=self.bg_main, 
                          font=("Arial", 10)).pack(anchor="w", pady=(0, 10))
            
            # 音效參數滑條
            self.sound_frequency_slider = self.create_slider(sound_frame, get_text("sound_frequency"), getattr(self.config, 'sound_frequency', 1000), 400, 2000, self.sound_frequency_configurator, res=50, val_format=".0f")
            self.sound_duration_slider = self.create_slider(sound_frame, get_text("sound_duration"), getattr(self.config, 'sound_duration', 100), 50, 500, self.sound_duration_configurator, res=10, val_format=".0f")
            self.sound_interval_slider = self.create_slider(sound_frame, get_text("sound_interval"), getattr(self.config, 'sound_interval', 200), 100, 1000, self.sound_interval_configurator, res=50, val_format=".0f")
        else:
            # 簡單模式下隱藏音效設置，設置為None以保持兼容性
            self.enable_sound_alert_var = tk.BooleanVar(value=getattr(self.config, 'enable_sound_alert', True))
            self.sound_frequency_slider = None
            self.sound_duration_slider = None
            self.sound_interval_slider = None

    def create_preset_management_tab(self, notebook):
        """建立預設管理分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_preset_management"))
        
        # 初始化預設管理器
        from preset_manager import PresetManager
        self.preset_manager = PresetManager()
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        # 主要容器，使用左右分佈
        main_container = tk.Frame(tab, bg=self.bg_main)
        main_container.pack(fill="both", expand=True)
        
        # 左側：預設列表
        left_frame = create_section_frame(main_container, get_text("preset_config"))
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 預設列表框架
        list_container = tk.Frame(left_frame, bg=self.bg_frame)
        list_container.pack(fill="both", expand=True)
        
        # 預設列表框架
        listbox_frame = tk.Frame(list_container, bg=self.bg_frame)
        listbox_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 預設列表
        self.preset_listbox = tk.Listbox(listbox_frame, 
                                        bg="#2a0a2a", 
                                        fg="white", 
                                        selectbackground="#4a2a4a", 
                                        selectforeground="white",
                                        font=("Arial", 11),
                                        height=15)
        self.preset_listbox.pack(side="left", fill="both", expand=True)
        
        # 滾動條
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.preset_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.preset_listbox.yview)
        
        # 當前選中顯示
        self.selected_preset_label = tk.Label(list_container, 
                                             text=f"{get_text('parameter_name')}：{get_text('no_selection')}", 
                                             bg=self.bg_frame, 
                                             fg="#cccccc", 
                                             font=("Arial", 9))
        self.selected_preset_label.pack(anchor="w", pady=(5, 0))
        
        # 右側：控制按鈕
        right_frame = create_section_frame(main_container, "管理功能")
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        
        # 按鈕樣式
        button_style = {
            "bg": "#4a2a4a",
            "fg": "white",
            "activebackground": "#6a4a6a",
            "activeforeground": "white",
            "font": ("Arial", 9, "bold"),
            "width": 12,
            "height": 2,
            "relief": "raised",
            "bd": 2
        }
        
        # 第一行按鈕
        row1_frame = tk.Frame(right_frame, bg=self.bg_frame)
        row1_frame.pack(pady=(10, 5))
        
        tk.Button(row1_frame, text=get_text("create_preset"), 
                 command=self.create_new_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        tk.Button(row1_frame, text=get_text("rename_preset"), 
                 command=self.rename_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        
        # 第二行按鈕
        row2_frame = tk.Frame(right_frame, bg=self.bg_frame)
        row2_frame.pack(pady=5)
        
        tk.Button(row2_frame, text=get_text("load_preset"), 
                 command=self.load_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        tk.Button(row2_frame, text=get_text("save_preset"), 
                 command=self.save_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        
        # 第三行按鈕
        row3_frame = tk.Frame(right_frame, bg=self.bg_frame)
        row3_frame.pack(pady=5)
        
        tk.Button(row3_frame, text=get_text("refresh_preset"), 
                 command=self.refresh_preset_list_tab, 
                 **button_style).pack(side="left", padx=2)
        tk.Button(row3_frame, text=get_text("delete_preset"), 
                 command=self.delete_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        
        # 第四行按鈕（文件操作）
        row4_frame = tk.Frame(right_frame, bg=self.bg_frame)
        row4_frame.pack(pady=(15, 5))
        
        tk.Button(row4_frame, text=get_text("open_preset_folder"), 
                 command=self.open_presets_folder_tab, 
                 bg="#2a4a2a", fg="white", activebackground="#4a6a4a", 
                 font=("Arial", 9, "bold"), width=25, height=1).pack()
        
        # 第五行按鈕（匯入匯出）
        row5_frame = tk.Frame(right_frame, bg=self.bg_frame)
        row5_frame.pack(pady=5)
        
        tk.Button(row5_frame, text=get_text("import_preset"), 
                 command=self.import_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        tk.Button(row5_frame, text=get_text("export_preset"), 
                 command=self.export_preset_tab, 
                 **button_style).pack(side="left", padx=2)
        
        # 底部說明
        info_frame = tk.Frame(right_frame, bg=self.bg_frame)
        info_frame.pack(pady=(20, 0), fill="x")
        
        info_text = "💡 使用說明：\n" \
                   "1. 選擇預設配置\n" \
                   "2. 點擊載入參數\n" \
                   "3. 設定自動應用"
        
        tk.Label(info_frame, text=info_text, 
                bg=self.bg_frame, fg="#888888", 
                font=("Arial", 8), justify="left").pack(anchor="w")
        
        # 綁定列表選擇事件
        self.preset_listbox.bind('<<ListboxSelect>>', self.on_preset_select_tab)
        
        # 初始化列表
        self.refresh_preset_list_tab()

    def create_program_control_tab(self, notebook):
        """建立程式控制分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_program_control"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        control_frame = create_section_frame(tab, get_text("program_control"))
        control_frame.pack(fill="x", pady=(0, 15))
        
        # 狀態顯示
        self.AimLabel = tk.Label(control_frame, text=f"{get_text('auto_aim')}: {get_text('status_panel_on') if self.config.AimToggle else get_text('status_panel_off')}", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 11))
        self.AimLabel.pack(pady=8)
        
        # 使用與狀態面板相同的邏輯來獲取運算模式文字
        provider_str = self.get_compute_mode_text()
        self.ProviderLabel = tk.Label(control_frame, text=f"{get_text('compute_mode')}: {provider_str}", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 11))
        self.ProviderLabel.pack(pady=8)
        
        # 控制按鈕
        btn_container = tk.Frame(control_frame, bg=self.bg_frame)
        btn_container.pack(pady=15)
        
        tk.Button(btn_container, text=get_text("toggle_auto_aim"), command=self.toggle_aim, bg=self.btn_bg, fg=self.fg_text, activebackground=self.btn_active, font=("Arial", 10), width=12, height=2).pack(side="left", padx=8)
        tk.Button(btn_container, text=get_text("about"), command=self.show_about, bg="#4CAF50", fg="white", activebackground="#45a049", font=("Arial", 10), width=12, height=2).pack(side="left", padx=8)
        tk.Button(btn_container, text=get_text("exit_and_save"), command=self.quit_program, bg=self.btn_bg, fg=self.fg_text, activebackground=self.btn_active, font=("Arial", 10), width=12, height=2).pack(side="left", padx=8)

    def create_slider(self, parent, text, default_val, from_, to, command, res: Union[int, float] = 1, val_format="", length=200, slider_name=""):
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        frame.pack(fill="x", pady=2)
        
        # 頂部框架：標籤文字 + 可編輯數值框
        top_frame = tk.Frame(frame, bg=parent.cget("bg"))
        top_frame.pack(fill="x", pady=(0, 2))
        
        # 標籤文字
        label = tk.Label(top_frame, text=f"{text}: ", bg=parent.cget("bg"), fg=self.fg_text)
        label.pack(side="left")
        
        # 可編輯的數值輸入框
        entry_var = tk.StringVar()
        initial_val = f"{default_val:{val_format}}" if val_format else str(int(default_val))
        entry_var.set(initial_val)
        
        entry = tk.Entry(top_frame, textvariable=entry_var, width=8, bg=self.bg_frame, fg=self.fg_text, 
                        insertbackground=self.fg_text, relief="solid", bd=2, font=("Arial", 9),
                        highlightbackground="#666666", highlightcolor="#888888", highlightthickness=1)
        entry.pack(side="left", padx=(5, 0))
        
        # 滑動條更新輸入框的函數
        def on_scale(val):
            new_val = float(val) if isinstance(res, float) else int(val)
            formatted_val = f"{new_val:{val_format}}" if val_format else str(int(new_val))
            entry_var.set(formatted_val)
            command(val)
        
        # 輸入框更新滑動條的函數
        def on_entry_change(*args):
            try:
                val_str = entry_var.get().strip()
                if val_str:
                    new_val = float(val_str)
                    # 限制在範圍內
                    new_val = max(from_, min(to, new_val))
                    # 根據解析度調整
                    if isinstance(res, float):
                        new_val = round(new_val / res) * res
                    else:
                        new_val = int(new_val)
                    
                    # 更新滑動條（不會觸發 on_scale，避免循環）
                    scale.set(new_val)
                    # 直接調用命令函數
                    command(str(new_val))
                    
                    # 確保輸入框顯示正確格式
                    formatted_val = f"{new_val:{val_format}}" if val_format else str(int(new_val))
                    if entry_var.get() != formatted_val:
                        entry_var.set(formatted_val)
            except ValueError:
                # 如果輸入無效，恢復到滑動條的當前值
                current_val = scale.get()
                formatted_val = f"{current_val:{val_format}}" if val_format else str(int(current_val))
                entry_var.set(formatted_val)
        
        # 綁定輸入框變化事件
        entry_var.trace_add("write", on_entry_change)
        
        # 綁定 Enter 鍵和失去焦點事件
        def on_entry_validate(event=None):
            on_entry_change()
        
        entry.bind("<Return>", on_entry_validate)
        entry.bind("<FocusOut>", on_entry_validate)

        scale = tk.Scale(frame, from_=from_, to=to, resolution=res, orient="horizontal", bg=parent.cget("bg"), fg=self.fg_text,
                         troughcolor=self.scale_trough, highlightbackground=self.bg_frame, activebackground=self.scale_slider,
                         command=on_scale, showvalue=False, length=length)
        scale.set(default_val)
        scale.pack(fill="x")

        return scale

    def quit_program(self):
        self.config.Running = False
        save_config(self.config)
        self.master.quit()
        self.master.destroy()

    def on_model_change(self, event=None):
        self.config.model_path = os.path.join('模型', self.model_var.get())
        if self.start_ai_threads: 
            self.start_ai_threads(self.config.model_path)
            # 延遲一下等待模型加載完成後更新狀態標籤
            self.master.after(1000, self.update_status_labels)

    def fov_size_configurator(self, v): self.config.fov_size = int(v)
    def min_confidence_configurator(self, v): self.config.min_confidence = float(v) / 100.0
    def detect_interval_configurator(self, v): self.config.detect_interval = int(v) / 1000.0
    def pid_kp_x_configurator(self, v): self.config.pid_kp_x = float(v)
    def pid_ki_x_configurator(self, v): self.config.pid_ki_x = float(v)
    def pid_kd_x_configurator(self, v): self.config.pid_kd_x = float(v)
    def pid_kp_y_configurator(self, v): self.config.pid_kp_y = float(v)
    def pid_ki_y_configurator(self, v): self.config.pid_ki_y = float(v)
    def pid_kd_y_configurator(self, v): self.config.pid_kd_y = float(v)
    def unified_pid_kp_configurator(self, v): 
        """統一PID P值配置器 - 同時設定X和Y軸"""
        value = float(v)
        self.config.pid_kp_x = value
        self.config.pid_kp_y = value
    def auto_fire_delay_configurator(self, v): self.config.auto_fire_delay = float(v)
    def auto_fire_interval_configurator(self, v): self.config.auto_fire_interval = float(v)

    # 目標區域占比配置方法
    def head_width_ratio_configurator(self, v): self.config.head_width_ratio = float(v) / 100.0
    def head_height_ratio_configurator(self, v): self.config.head_height_ratio = float(v) / 100.0
    def body_width_ratio_configurator(self, v): self.config.body_width_ratio = float(v) / 100.0
    
    # ***** 新增：音效提示系統配置方法 *****
    def sound_frequency_configurator(self, v): self.config.sound_frequency = int(v)
    def sound_duration_configurator(self, v): self.config.sound_duration = int(v)  
    def sound_interval_configurator(self, v): self.config.sound_interval = int(v)
    
    def toggle_aim(self):
        self.config.AimToggle = not self.config.AimToggle
        if hasattr(self, 'AimLabel'):
            status_text = get_text('status_panel_on') if self.config.AimToggle else get_text('status_panel_off')
            self.AimLabel.config(text=f"{get_text('auto_aim')}: {status_text}")
    def toggle_show_confidence(self): self.config.show_confidence = self.show_confidence_var.get()
    def toggle_show_fov(self): self.config.show_fov = self.show_fov_var.get()
    def toggle_show_boxes(self): self.config.show_boxes = self.show_boxes_var.get()
    def toggle_keep_detecting(self): self.config.keep_detecting = self.keep_detecting_var.get()
    def toggle_fov_follow_mouse(self): self.config.fov_follow_mouse = self.fov_follow_mouse_var.get()
    

    
    def aim_part_changed(self, var_name=None, index=None, mode=None): 
        # 將顯示的中文文字轉換為內部使用的英文值
        display_value = self.AimPartVar.get()
        if display_value == get_text("head"):  # "頭部"
            self.config.aim_part = "head"
        elif display_value == get_text("body"):  # "身體"
            self.config.aim_part = "body"
        else:
            # 向後兼容，如果已經是英文值就直接使用
            self.config.aim_part = display_value
    
    def auto_fire_part_changed(self, var_name=None, index=None, mode=None): 
        # 將顯示的中文文字轉換為內部使用的英文值
        display_value = self.AutoFirePartVar.get()
        if display_value == get_text("head"):  # "頭部"
            self.config.auto_fire_target_part = "head"
        elif display_value == get_text("body"):  # "身體"
            self.config.auto_fire_target_part = "body"
        elif display_value == get_text("both"):  # "兩者"
            self.config.auto_fire_target_part = "both"
        else:
            # 向後兼容，如果已經是英文值就直接使用
            self.config.auto_fire_target_part = display_value
    
    def get_key_name(self, key_code):
        return get_vk_name(key_code)

    def update_key_buttons(self):
        # 確保 AimKeys 至少有3個元素
        while len(self.config.AimKeys) < 3:
            self.config.AimKeys.append(0x02)  # 默認添加右鍵
            
        self.key_buttons[1].config(text=self.get_key_name(self.config.AimKeys[0]))
        self.key_buttons[2].config(text=self.get_key_name(self.config.AimKeys[1]))
        if 6 in self.key_buttons:  # 檢查第三個瞄準按鍵是否存在
            self.key_buttons[6].config(text=self.get_key_name(self.config.AimKeys[2]))
        self.key_buttons[3].config(text=self.get_key_name(self.config.auto_fire_key))
        self.key_buttons[4].config(text=self.get_key_name(self.config.aim_toggle_key))
        self.key_buttons[5].config(text=self.get_key_name(getattr(self.config, 'auto_fire_key2', 0x58)))

    def start_listening(self, slot):
        if self.listening_for_slot is not None:
            self.update_key_buttons()
        self.listening_for_slot = slot
        self.key_buttons[slot].config(text=get_text('key_listening'))

    def key_listener(self):
        if self.listening_for_slot is not None:
            detected_key = None
            for key_code in [1, 2, 4, 5, 6, *range(8, 256)]:
                if win32api.GetAsyncKeyState(key_code) & 0x8000:
                    detected_key = key_code
                    break
            
            if detected_key:
                slot = self.listening_for_slot
                if slot == 1: self.config.AimKeys[0] = detected_key
                elif slot == 2: self.config.AimKeys[1] = detected_key
                elif slot == 6: 
                    # 確保 AimKeys 至少有3個元素
                    while len(self.config.AimKeys) < 3:
                        self.config.AimKeys.append(0x02)
                    self.config.AimKeys[2] = detected_key
                elif slot == 3: self.config.auto_fire_key = detected_key
                elif slot == 4: self.config.aim_toggle_key = detected_key
                elif slot == 5: self.config.auto_fire_key2 = detected_key
                
                self.listening_for_slot = None
                self.update_key_buttons()

        self.master.after(20, self.key_listener)

    def poll_aimtoggle_status(self):
        if hasattr(self, 'AimLabel'):
            status_text = get_text('status_panel_on') if self.config.AimToggle else get_text('status_panel_off')
            label_text = f"{get_text('auto_aim')}: {status_text}"
            if self.AimLabel.cget("text") != label_text:
                self.AimLabel.config(text=label_text)
        self.master.after(100, self.poll_aimtoggle_status)

    def toggle_language(self):
        """切換語言"""
        current_lang = self.language_manager.get_current_language()
        new_lang = "en" if current_lang == "zh_tw" else "zh_tw"
        self.language_manager.set_language(new_lang)
        self.refresh_ui_text()

    def toggle_mode(self):
        """切換高級/簡單模式"""
        self.config.advanced_mode = not getattr(self.config, 'advanced_mode', True)
        
        # 更新按鈕文字
        mode_text = get_text("simple_mode") if self.config.advanced_mode else get_text("advanced_mode")
        self.mode_button.config(text=mode_text)
        
        # 更新介面可見性
        self.update_mode_visibility()
        
        # 儲存配置
        save_config(self.config)
        
        print(f"已切換至{'高級' if self.config.advanced_mode else '簡單'}模式")

    def update_mode_visibility(self):
        """根據當前模式更新介面元素的可見性"""
        is_advanced = getattr(self.config, 'advanced_mode', True)
        
        # 簡單模式下隱藏預設管理分頁
        if not is_advanced:
            try:
                # 隱藏預設管理分頁
                if self.preset_management_tab_index < len(self.main_notebook.tabs()):
                    self.main_notebook.hide(self.preset_management_tab_index)
            except Exception as e:
                print(f"隱藏預設管理分頁時發生錯誤: {e}")
        else:
            try:
                # 顯示預設管理分頁
                if self.preset_management_tab_index < len(self.main_notebook.tabs()):
                    tab_id = self.main_notebook.tabs()[self.preset_management_tab_index]
                    if tab_id not in [self.main_notebook.tabs()[i] for i in range(len(self.main_notebook.tabs())) if self.main_notebook.tab(i, "state") != "hidden"]:
                        self.main_notebook.add(self.main_notebook.nametowidget(tab_id), text=get_text("tab_preset_management"))
            except Exception as e:
                print(f"顯示預設管理分頁時發生錯誤: {e}")
        
        # 重新創建分頁以應用模式變更
        self.recreate_tabs_for_mode_change()

    def recreate_tabs_for_mode_change(self):
        """重新創建分頁以應用模式變更"""
        try:
            # 保存當前選中的分頁索引
            current_tab = self.main_notebook.index(self.main_notebook.select())
            
            # 清除所有分頁
            for tab in self.main_notebook.tabs():
                self.main_notebook.forget(tab)
            
            # 重新創建分頁
            self.create_basic_settings_tab(self.main_notebook)
            self.create_aim_control_tab(self.main_notebook)
            self.create_keys_settings_tab(self.main_notebook)
            self.create_auto_features_tab(self.main_notebook)
            self.create_display_options_tab(self.main_notebook)
            
            # 只在高級模式下添加預設管理分頁
            is_advanced = getattr(self.config, 'advanced_mode', True)
            if is_advanced:
                self.create_preset_management_tab(self.main_notebook)
            
            self.create_program_control_tab(self.main_notebook)
            
            # 恢復選中的分頁（如果可能）
            try:
                if current_tab < len(self.main_notebook.tabs()):
                    self.main_notebook.select(current_tab)
                else:
                    self.main_notebook.select(0)
            except:
                self.main_notebook.select(0)
                
        except Exception as e:
            print(f"重新創建分頁時發生錯誤: {e}")

    def refresh_ui_text(self):
        """刷新所有UI文字"""
        self.master.title(get_text("window_title"))
        # 更新語言切換按鈕文字
        current_lang = self.language_manager.get_current_language()
        button_text = get_text("english") if current_lang == "zh_tw" else get_text("chinese")
        self.lang_button.config(text=button_text)
        donate_text = get_text("donate") if current_lang == "zh_tw" else get_text("donate_en")
        self.donate_button.config(text=donate_text)
        # 更新模式切換按鈕文字
        mode_text = get_text("simple_mode") if getattr(self.config, 'advanced_mode', True) else get_text("advanced_mode")
        self.mode_button.config(text=mode_text)
        self.restart_gui()

    def restart_gui(self):
        """重新啟動GUI以應用新語言"""
        save_config(self.config)
        self.master.destroy()
        # 避免循環導入，直接調用模組級別的函數
        create_settings_gui(self.config, self.start_ai_threads)

    def update_status_labels(self):
        """更新狀態標籤文字"""
        aim_status = get_text("status_panel_on") if self.config.AimToggle else get_text("status_panel_off")
        self.AimLabel.config(text=f"{get_text('auto_aim')}: {aim_status}")
        provider_str = self.get_compute_mode_text()
        self.ProviderLabel.config(text=f"{get_text('compute_mode')}: {provider_str}")

    def open_donate_page(self):
        os.startfile(os.path.join(os.path.dirname(__file__), 'MVP.html'))
    
    def show_about(self):
        """顯示關於視窗"""
        show_about_window(self.master)

    def toggle_single_target_mode(self):
        self.config.single_target_mode = self.single_target_var.get()

    def toggle_sound_alert(self):
        """切換音效提示"""
        self.config.enable_sound_alert = self.enable_sound_alert_var.get()
    
    def open_preset_manager(self):
        """打開預設管理器（向後兼容）"""
        # 這個方法保留是為了向後兼容，但現在會切換到預設管理標籤頁
        messagebox.showinfo("提示", "預設管理功能現在已整合到「預設管理」標籤頁中！")
    
    def update_gui_from_preset(self):
        """從預設配置更新GUI顯示"""
        try:
            print("開始更新GUI...")
            
            # 更新模型選擇
            if hasattr(self, 'model_var'):
                model_name = os.path.basename(self.config.model_path)
                self.model_var.set(model_name)
                print(f"已更新模型: {model_name}")
            
            # 更新滑條值 - 需要觸發更新事件
            # FOV大小
            if hasattr(self, 'fov_size_slider'):
                self.fov_size_slider.set(self.config.fov_size)
            
            # 最小置信度
            if hasattr(self, 'min_confidence_slider'):
                self.min_confidence_slider.set(self.config.min_confidence * 100)
            
            # 檢測間隔
            if hasattr(self, 'detect_interval_slider'):
                self.detect_interval_slider.set(self.config.detect_interval * 1000)
            
            # PID 參數
            if hasattr(self, 'pid_kp_x_slider'):
                self.pid_kp_x_slider.set(self.config.pid_kp_x)
            if hasattr(self, 'pid_ki_x_slider'):
                self.pid_ki_x_slider.set(self.config.pid_ki_x)
            if hasattr(self, 'pid_kd_x_slider'):
                self.pid_kd_x_slider.set(self.config.pid_kd_x)
            if hasattr(self, 'pid_kp_y_slider'):
                self.pid_kp_y_slider.set(self.config.pid_kp_y)
            if hasattr(self, 'pid_ki_y_slider'):
                self.pid_ki_y_slider.set(self.config.pid_ki_y)
            if hasattr(self, 'pid_kd_y_slider'):
                self.pid_kd_y_slider.set(self.config.pid_kd_y)
                
            # 頭部和身體占比參數
            if hasattr(self, 'head_width_ratio_slider'):
                self.head_width_ratio_slider.set(getattr(self.config, 'head_width_ratio', 0.38) * 100)
            if hasattr(self, 'head_height_ratio_slider'):
                self.head_height_ratio_slider.set(getattr(self.config, 'head_height_ratio', 0.26) * 100)
            if hasattr(self, 'body_width_ratio_slider'):
                self.body_width_ratio_slider.set(getattr(self.config, 'body_width_ratio', 0.87) * 100)
                
            # 自動開火參數
            if hasattr(self, 'auto_fire_delay_slider'):
                self.auto_fire_delay_slider.set(getattr(self.config, 'auto_fire_delay', 0.0))
            if hasattr(self, 'auto_fire_interval_slider'):
                self.auto_fire_interval_slider.set(getattr(self.config, 'auto_fire_interval', 0.18))
                
            # 防後座力參數

                
            # 音效提示系統參數
            if hasattr(self, 'sound_frequency_slider'):
                self.sound_frequency_slider.set(getattr(self.config, 'sound_frequency', 1000))
            if hasattr(self, 'sound_duration_slider'):
                self.sound_duration_slider.set(getattr(self.config, 'sound_duration', 100))
            if hasattr(self, 'sound_interval_slider'):
                self.sound_interval_slider.set(getattr(self.config, 'sound_interval', 200))
            
            # 更新瞄準部位
            if hasattr(self, 'AimPartVar'):
                display_aim_part = self.config.aim_part
                if self.config.aim_part == "head":
                    display_aim_part = get_text("head")
                elif self.config.aim_part == "body":
                    display_aim_part = get_text("body")
                self.AimPartVar.set(display_aim_part)
                print(f"已更新瞄準部位: {display_aim_part}")
            
            # 更新自動開火部位
            if hasattr(self, 'AutoFirePartVar'):
                display_autofire_part = self.config.auto_fire_target_part
                if self.config.auto_fire_target_part == "head":
                    display_autofire_part = get_text("head")
                elif self.config.auto_fire_target_part == "body":
                    display_autofire_part = get_text("body")
                elif self.config.auto_fire_target_part == "both":
                    display_autofire_part = get_text("both")
                self.AutoFirePartVar.set(display_autofire_part)
                print(f"已更新自動開火部位: {display_autofire_part}")
            
            # 更新復選框狀態
            if hasattr(self, 'show_confidence_var'):
                self.show_confidence_var.set(self.config.show_confidence)
            if hasattr(self, 'show_fov_var'):
                self.show_fov_var.set(getattr(self.config, 'show_fov', True))
            if hasattr(self, 'show_boxes_var'):
                self.show_boxes_var.set(getattr(self.config, 'show_boxes', True))
            if hasattr(self, 'keep_detecting_var'):
                self.keep_detecting_var.set(getattr(self.config, 'keep_detecting', True))
            if hasattr(self, 'fov_follow_mouse_var'):
                self.fov_follow_mouse_var.set(getattr(self.config, 'fov_follow_mouse', False))

            if hasattr(self, 'single_target_var'):
                self.single_target_var.set(getattr(self.config, 'single_target_mode', True))
            if hasattr(self, 'enable_sound_alert_var'):
                self.enable_sound_alert_var.set(getattr(self.config, 'enable_sound_alert', True))
            
            # 更新按鍵顯示
            self.update_key_buttons()
            
            # 更新狀態標籤
            if hasattr(self, 'update_status_labels'):
                self.update_status_labels()
            
            # 如果有模型更改，重新載入模型
            if hasattr(self, 'start_ai_threads') and self.start_ai_threads:
                self.start_ai_threads(self.config.model_path)
                
            print("GUI 更新完成")
            
        except Exception as e:
            print(f"更新GUI失敗: {e}")
            import traceback
            traceback.print_exc()

    # ***** 新增：預設管理標籤頁功能方法 *****
    def refresh_preset_list_tab(self):
        """刷新預設列表"""
        if hasattr(self, 'preset_listbox'):
            self.preset_listbox.delete(0, tk.END)
            presets = self.preset_manager.get_preset_list()
            for preset in presets:
                self.preset_listbox.insert(tk.END, preset)
    
    def on_preset_select_tab(self, event):
        """處理預設選擇事件"""
        selection = self.preset_listbox.curselection()
        if selection:
            preset_name = self.preset_listbox.get(selection[0])
            self.selected_preset_label.config(text=f"{get_text('parameter_name')}：{preset_name}")
    
    def get_selected_preset_tab(self):
        """獲取當前選中的預設"""
        if hasattr(self, 'preset_listbox'):
            selection = self.preset_listbox.curselection()
            if selection:
                return self.preset_listbox.get(selection[0])
        return None
    
    def create_new_preset_tab(self):
        """創建新預設"""
        import tkinter.simpledialog as simpledialog
        name = simpledialog.askstring("新建預設", "請輸入預設名稱:")
        if name:
            if self.preset_manager.save_preset(self.config, name):
                messagebox.showinfo("成功", f"預設 '{name}' 創建成功!")
                self.refresh_preset_list_tab()
            else:
                messagebox.showerror("錯誤", "創建預設失敗!")
    
    def rename_preset_tab(self):
        """重命名預設"""
        import tkinter.simpledialog as simpledialog
        old_name = self.get_selected_preset_tab()
        if not old_name:
            messagebox.showwarning("警告", "請先選擇一個預設!")
            return
        
        new_name = simpledialog.askstring("重命名預設", f"重命名 '{old_name}' 為:", initialvalue=old_name)
        if new_name and new_name != old_name:
            if self.preset_manager.rename_preset(old_name, new_name):
                messagebox.showinfo("成功", f"預設重命名為 '{new_name}' 成功!")
                self.refresh_preset_list_tab()
            else:
                messagebox.showerror("錯誤", "重命名預設失敗!")
    
    def load_preset_tab(self):
        """載入預設"""
        preset_name = self.get_selected_preset_tab()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個預設!")
            return
        
        if self.preset_manager.load_preset(self.config, preset_name):
            self.update_gui_from_preset()
            save_config(self.config)
            messagebox.showinfo("成功", f"預設 '{preset_name}' 載入成功!\n所有設定已更新。")
        else:
            messagebox.showerror("錯誤", "載入預設失敗!")
    
    def save_preset_tab(self):
        """保存當前配置為預設"""
        preset_name = self.get_selected_preset_tab()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個預設或創建新預設!")
            return
        
        result = messagebox.askyesno("確認", f"確定要用當前配置覆蓋預設 '{preset_name}' 嗎?")
        if result:
            if self.preset_manager.save_preset(self.config, preset_name):
                messagebox.showinfo("成功", f"預設 '{preset_name}' 保存成功!")
            else:
                messagebox.showerror("錯誤", "保存預設失敗!")
    
    def delete_preset_tab(self):
        """刪除預設"""
        preset_name = self.get_selected_preset_tab()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個預設!")
            return
        
        result = messagebox.askyesno("確認刪除", f"確定要刪除預設 '{preset_name}' 嗎?\n此操作無法復原!")
        if result:
            if self.preset_manager.delete_preset(preset_name):
                messagebox.showinfo("成功", f"預設 '{preset_name}' 刪除成功!")
                self.refresh_preset_list_tab()
                self.selected_preset_label.config(text=f"{get_text('parameter_name')}：{get_text('no_selection')}")
            else:
                messagebox.showerror("錯誤", "刪除預設失敗!")
    
    def open_presets_folder_tab(self):
        """打開預設文件夾"""
        import subprocess
        import platform
        
        preset_path = os.path.abspath(self.preset_manager.presets_dir)
        
        try:
            if platform.system() == "Windows":
                os.startfile(preset_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", preset_path])
            else:  # Linux
                subprocess.run(["xdg-open", preset_path])
        except Exception as e:
            messagebox.showerror("錯誤", f"無法打開文件夾: {e}")
    
    def import_preset_tab(self):
        """匯入預設配置"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="選擇要匯入的配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            result = self.preset_manager.import_preset(file_path)
            if result:
                messagebox.showinfo("成功", f"配置匯入成功，名稱為: {result}")
                self.refresh_preset_list_tab()
            else:
                messagebox.showerror("錯誤", "匯入配置失敗!")
    
    def export_preset_tab(self):
        """匯出預設配置"""
        from tkinter import filedialog
        preset_name = self.get_selected_preset_tab()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個預設!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="選擇匯出位置",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue=f"{preset_name}.json"
        )
        
        if file_path:
            if self.preset_manager.export_preset(preset_name, file_path):
                messagebox.showinfo("成功", f"預設 '{preset_name}' 匯出成功!")
            else:
                messagebox.showerror("錯誤", "匯出預設失敗!")

    def get_compute_mode_text(self):
        """取得目前運算模式文字（如 CPU/GPU）"""
        provider = getattr(self.config, 'current_provider', 'CPUExecutionProvider')
        if provider == 'CPUExecutionProvider':
            return 'CPU'
        elif provider == 'CUDAExecutionProvider':
            return 'GPU (CUDA)'
        elif provider == 'DmlExecutionProvider':
            return 'GPU (DirectML)'
        else:
            return str(provider)

def create_settings_gui(config, start_ai_threads=None):
    root = tk.Tk()
    app = SettingsWindow(root, config, start_ai_threads)
    root.mainloop()

if __name__ == "__main__":
    # 測試用的main函數
    from config import Config
    test_config = Config()
    create_settings_gui(test_config)