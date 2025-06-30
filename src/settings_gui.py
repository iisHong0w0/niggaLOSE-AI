# settings_gui.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import win32api
import glob
import math
from typing import Union

# 從我們自己建立的模組中導入
from win_utils import VK_CODE_MAP, get_vk_name
from config import save_config
from language_manager import language_manager, get_text  # 新增導入
from about import show_about_window  # 導入關於視窗

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
        self.master.geometry('999x999')
        self.master.protocol("WM_DELETE_WINDOW", self.quit_program)

        # --- 顏色與樣式 (設定為實例屬性) ---
        self.bg_main = "#250526"
        self.bg_frame = '#120606'
        self.fg_text = '#e0e6f0'
        self.accent = '#230622'
        self.btn_bg = '#230622'
        self.btn_active = '#230622'
        self.scale_trough = '#230622'
        self.scale_slider = '#230622'

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
        self.lang_button.pack(side="right", pady=5)
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
        main_notebook = ttk.Notebook(main_frame)
        main_notebook.pack(fill="both", expand=True, pady=10)

        # 建立各個分頁
        self.create_basic_settings_tab(main_notebook)
        self.create_aim_control_tab(main_notebook)
        self.create_keys_settings_tab(main_notebook)
        self.create_auto_features_tab(main_notebook)
        self.create_display_options_tab(main_notebook)
        self.create_program_control_tab(main_notebook)

        self.listening_for_slot = None
        self.key_listener()
        self.poll_aimtoggle_status()
        self.toggle_anti_recoil(init=True)
        
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
        
        self.create_slider(params_frame, get_text("fov_size"), self.config.fov_size, 50, min(self.config.width, self.config.height), self.fov_size_configurator)
        self.create_slider(params_frame, get_text("min_confidence"), self.config.min_confidence * 100, 0, 100, self.min_confidence_configurator)
        self.create_slider(params_frame, get_text("detect_interval"), self.config.detect_interval * 1000, 1, 100, self.detect_interval_configurator)
    
    def create_aim_control_tab(self, notebook):
        """建立瞄準控制分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_aim_control"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        # PID 控制器
        pid_frame = create_section_frame(tab, get_text("aim_speed_pid"))
        pid_frame.pack(fill="x", pady=(0, 15))

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
        
        self.create_slider(tab_x, get_text("reaction_speed_p"), self.config.pid_kp_x, 0, 1, self.pid_kp_x_configurator, res=0.001, val_format=".3f", length=400)
        self.create_slider(tab_x, get_text("error_correction_i"), self.config.pid_ki_x, 0, 0.1, self.pid_ki_x_configurator, res=0.001, val_format=".3f", length=400)
        self.create_slider(tab_x, get_text("stability_suppression_d"), self.config.pid_kd_x, 0, 0.2, self.pid_kd_x_configurator, res=0.001, val_format=".3f", length=400)

        self.create_slider(tab_y, get_text("reaction_speed_p"), self.config.pid_kp_y, 0, 1, self.pid_kp_y_configurator, res=0.001, val_format=".3f", length=400)
        self.create_slider(tab_y, get_text("error_correction_i"), self.config.pid_ki_y, 0, 0.1, self.pid_ki_y_configurator, res=0.001, val_format=".3f", length=400)
        self.create_slider(tab_y, get_text("stability_suppression_d"), self.config.pid_kd_y, 0, 0.2, self.pid_kd_y_configurator, res=0.001, val_format=".3f", length=400)
        
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
        
        # 目標區域設定
        area_frame = create_section_frame(tab, get_text("target_area_settings"))
        area_frame.pack(fill="x")
        
        area_left = tk.Frame(area_frame, bg=self.bg_frame)
        area_right = tk.Frame(area_frame, bg=self.bg_frame)
        area_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        area_right.pack(side="right", fill="both", expand=True)
        
        # 頭部設定
        tk.Label(area_left, text="頭部區域:", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.create_slider(area_left, get_text("head_width_ratio"), self.config.head_width_ratio * 100, 10, 100, self.head_width_ratio_configurator, res=1, val_format=".0f")
        self.create_slider(area_left, get_text("head_height_ratio"), self.config.head_height_ratio * 100, 10, 50, self.head_height_ratio_configurator, res=1, val_format=".0f")
        
        # 身體設定
        tk.Label(area_right, text="身體區域:", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.create_slider(area_right, get_text("body_width_ratio"), self.config.body_width_ratio * 100, 50, 100, self.body_width_ratio_configurator, res=1, val_format=".0f")
        
        # 添加說明文字
        tk.Label(area_right, text="※ 身體高度 = 100% - 頭部高度", bg=self.bg_frame, fg="#888888", font=("Arial", 8)).pack(anchor="w", pady=(5, 0))

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

        self.create_slider(autofire_frame, get_text("scope_delay"), self.config.auto_fire_delay, 0, 1, self.auto_fire_delay_configurator, res=0.01, val_format=".2f")
        self.create_slider(autofire_frame, get_text("fire_interval"), self.config.auto_fire_interval, 0, 1, self.auto_fire_interval_configurator, res=0.01, val_format=".2f")
        
        # 防後座力設定
        recoil_frame = create_section_frame(tab, get_text("enable_anti_recoil"))
        recoil_frame.pack(fill="x")
        
        self.enable_anti_recoil_var = tk.BooleanVar(value=self.config.enable_anti_recoil)
        tk.Checkbutton(recoil_frame, text=get_text("enable_anti_recoil"), variable=self.enable_anti_recoil_var, command=self.toggle_anti_recoil, bg=self.bg_frame, fg=self.fg_text, selectcolor=self.bg_main, font=("Arial", 10)).pack(anchor="w", pady=(0, 10))
        
        self.create_slider(recoil_frame, get_text("anti_recoil_speed"), self.config.anti_recoil_speed, 0, 10, self.anti_recoil_speed_configurator, res=0.1, val_format=".1f")

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

    def create_program_control_tab(self, notebook):
        """建立程式控制分頁"""
        tab = tk.Frame(notebook, bg=self.bg_main, padx=20, pady=15)
        notebook.add(tab, text=get_text("tab_program"))
        
        def create_section_frame(parent, title):
            return tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), 
                                 bg=self.bg_frame, fg=self.fg_text, bd=2, relief="groove",
                                 labelanchor="n", padx=15, pady=10)
        
        control_frame = create_section_frame(tab, get_text("program_control"))
        control_frame.pack(fill="x", pady=(0, 15))
        
        # 狀態顯示
        self.AimLabel = tk.Label(control_frame, text=f"{get_text('auto_aim')}: {get_text('status_panel_on') if self.config.AimToggle else get_text('status_panel_off')}", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 11))
        self.AimLabel.pack(pady=8)
        
        provider_str = get_text("gpu_directml") if "Dml" in self.config.current_provider else get_text("cpu")
        self.ProviderLabel = tk.Label(control_frame, text=f"{get_text('compute_mode')}: {provider_str}", bg=self.bg_frame, fg=self.fg_text, font=("Arial", 11))
        self.ProviderLabel.pack(pady=8)
        
        # 控制按鈕
        btn_container = tk.Frame(control_frame, bg=self.bg_frame)
        btn_container.pack(pady=15)
        
        tk.Button(btn_container, text=get_text("toggle_auto_aim"), command=self.toggle_aim, bg=self.btn_bg, fg=self.fg_text, activebackground=self.btn_active, font=("Arial", 10), width=12, height=2).pack(side="left", padx=8)
        tk.Button(btn_container, text=get_text("about"), command=self.show_about, bg="#4CAF50", fg="white", activebackground="#45a049", font=("Arial", 10), width=12, height=2).pack(side="left", padx=8)
        tk.Button(btn_container, text=get_text("exit_and_save"), command=self.quit_program, bg=self.btn_bg, fg=self.fg_text, activebackground=self.btn_active, font=("Arial", 10), width=12, height=2).pack(side="left", padx=8)

    def create_slider(self, parent, text, default_val, from_, to, command, res: Union[int, float] = 1, val_format="", length=200):
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
    def auto_fire_delay_configurator(self, v): self.config.auto_fire_delay = float(v)
    def auto_fire_interval_configurator(self, v): self.config.auto_fire_interval = float(v)
    def anti_recoil_speed_configurator(self, v): self.config.anti_recoil_speed = float(v)
    
    # 目標區域占比配置方法
    def head_width_ratio_configurator(self, v): self.config.head_width_ratio = float(v) / 100.0
    def head_height_ratio_configurator(self, v): self.config.head_height_ratio = float(v) / 100.0
    def body_width_ratio_configurator(self, v): self.config.body_width_ratio = float(v) / 100.0
    
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
    
    def toggle_anti_recoil(self, init=False):
        is_enabled = self.enable_anti_recoil_var.get()
        if not init:
            self.config.enable_anti_recoil = is_enabled
        
        if is_enabled:
            self.fov_follow_mouse_var.set(False)
            self.config.fov_follow_mouse = False
            self.fov_follow_mouse_checkbox.config(state="disabled")
        else:
            self.fov_follow_mouse_checkbox.config(state="normal")
    
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

    def refresh_ui_text(self):
        """刷新所有UI文字"""
        self.master.title(get_text("window_title"))
        # 更新語言切換按鈕文字
        current_lang = self.language_manager.get_current_language()
        button_text = get_text("english") if current_lang == "zh_tw" else get_text("chinese")
        self.lang_button.config(text=button_text)
        donate_text = get_text("donate") if current_lang == "zh_tw" else get_text("donate_en")
        self.donate_button.config(text=donate_text)
        self.restart_gui()

    def restart_gui(self):
        """重新啟動GUI以應用新語言"""
        save_config(self.config)
        self.master.destroy()
        from settings_gui import create_settings_gui
        create_settings_gui(self.config, self.start_ai_threads)

    def update_status_labels(self):
        """更新狀態標籤文字"""
        aim_status = get_text("status_panel_on") if self.config.AimToggle else get_text("status_panel_off")
        self.AimLabel.config(text=f"{get_text('auto_aim')}: {aim_status}")
        provider_str = get_text("gpu_directml") if "Dml" in self.config.current_provider else get_text("cpu")
        self.ProviderLabel.config(text=f"{get_text('compute_mode')}: {provider_str}")

    def open_donate_page(self):
        os.startfile(os.path.join(os.path.dirname(__file__), 'MVP.html'))
    
    def show_about(self):
        """顯示關於視窗"""
        show_about_window(self.master)

def create_settings_gui(config, start_ai_threads=None):
    root = tk.Tk()
    app = SettingsWindow(root, config, start_ai_threads)
    root.mainloop()