# about.py
import tkinter as tk
from tkinter import ttk
import webbrowser
import os
from PIL import Image, ImageTk
from language_manager import get_text

# PIL 兼容性處理
try:
    LANCZOS_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS_FILTER = Image.LANCZOS

class AboutWindow:
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title(get_text("about_title"))
        self.window.geometry('500x400')
        self.window.resizable(False, False)
        
        # 顏色設定 (與主程式保持一致)
        self.bg_main = "#250526"
        self.bg_frame = '#120606'
        self.fg_text = '#e0e6f0'
        self.accent = '#230622'
        self.btn_bg = '#230622'
        self.btn_active = '#FF0000'
        
        self.window.configure(bg=self.bg_main)
        
        # 設定視窗icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'logo.ico')
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
        
        # 使視窗置中
        self.center_window()
        
        # 創建內容
        self.create_widgets()
        
        # 設定為模態視窗
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        # 綁定關閉事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def center_window(self):
        """將視窗置中顯示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """創建視窗內容"""
        main_frame = tk.Frame(self.window, bg=self.bg_main, padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Logo區域
        logo_frame = tk.Frame(main_frame, bg=self.bg_main)
        logo_frame.pack(pady=(0, 20))
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((80, 80), LANCZOS_FILTER)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                tk.Label(logo_frame, image=self.logo_photo, bg=self.bg_main).pack()
        except:
            # 如果載入logo失敗，顯示文字替代
            tk.Label(logo_frame, text="Axiom V4", font=("Arial", 20, "bold"), 
                    bg=self.bg_main, fg=self.fg_text).pack()
        
        # 專案標題
        title_label = tk.Label(main_frame, text="Axiom V4", 
                              font=("Arial", 24, "bold"), 
                              bg=self.bg_main, fg=self.fg_text)
        title_label.pack(pady=(0, 10))
        
        # 副標題
        subtitle_label = tk.Label(main_frame, text=get_text("about_subtitle"), 
                                 font=("Arial", 12), 
                                 bg=self.bg_main, fg="#CCCCCC")
        subtitle_label.pack(pady=(0, 20))
        
        # 分隔線
        separator = tk.Frame(main_frame, height=2, bg=self.accent)
        separator.pack(fill="x", pady=15)
        
        # "我是人類"文字
        human_label = tk.Label(main_frame, text=get_text("i_am_human"), 
                              font=("Arial", 16, "bold"), 
                              bg=self.bg_main, fg=self.fg_text)
        human_label.pack(pady=(10, 20))
        
        # 按鈕區域
        button_frame = tk.Frame(main_frame, bg=self.bg_main)
        button_frame.pack(pady=15)
        
        # Discord 按鈕
        discord_btn = tk.Button(button_frame, 
                               text=f"💬 {get_text('join_discord')}", 
                               command=self.open_discord,
                               bg="#5865F2", 
                               fg="white",
                               font=("Arial", 11, "bold"),
                               relief="flat",
                               padx=20,
                               pady=10,
                               cursor="hand2")
        discord_btn.pack(side="left", padx=(0, 15))
        
        # GitHub 按鈕
        github_btn = tk.Button(button_frame, 
                              text=f"⭐ {get_text('view_github')}", 
                              command=self.open_github,
                              bg="#24292e", 
                              fg="white",
                              font=("Arial", 11, "bold"),
                              relief="flat",
                              padx=20,
                              pady=10,
                              cursor="hand2")
        github_btn.pack(side="left")
        
        # 關閉按鈕
        close_btn = tk.Button(main_frame, 
                             text=get_text("close"), 
                             command=self.on_close,
                             bg=self.btn_bg, 
                             fg=self.fg_text,
                             font=("Arial", 10),
                             relief="flat",
                             padx=30,
                             pady=8,
                             cursor="hand2")
        close_btn.pack(pady=(20, 0))
        
        # 版本資訊
        version_label = tk.Label(main_frame, text=get_text("version_info"), 
                                font=("Arial", 9), 
                                bg=self.bg_main, fg="#888888")
        version_label.pack(pady=(15, 0))
        
        # 鼠標懸停效果
        self.add_hover_effects(discord_btn, "#4752C4", "#5865F2")
        self.add_hover_effects(github_btn, "#1a1f23", "#24292e")
        self.add_hover_effects(close_btn, self.btn_active, self.btn_bg)
    
    def add_hover_effects(self, button, hover_color, normal_color):
        """為按鈕添加鼠標懸停效果"""
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def open_discord(self):
        """開啟Discord連結"""
        webbrowser.open("https://discord.gg/h4dEh3b8Bt")
    
    def open_github(self):
        """開啟GitHub連結"""
        webbrowser.open("https://github.com/iisHong0w0/Axiom-AI_Aimbot")
    
    def on_close(self):
        """關閉視窗"""
        if self.parent:
            self.window.grab_release()
        self.window.destroy()
    
    def show(self):
        """顯示視窗"""
        self.window.mainloop()

def show_about_window(parent=None):
    """顯示關於視窗的便捷函數"""
    about = AboutWindow(parent)
    return about

# 如果直接執行此檔案，顯示關於視窗
if __name__ == "__main__":
    about = AboutWindow()
    about.show() 