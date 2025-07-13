# preset_manager.py
import json
import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from config import Config, save_config, load_config
from language_manager import get_text

class PresetManager:
    def __init__(self):
        self.presets_dir = "presets"
        self.ensure_presets_directory()
        
    def ensure_presets_directory(self):
        """確保參數配置目錄存在"""
        if not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir)
            
    def get_preset_list(self):
        """獲取所有參數配置列表"""
        if not os.path.exists(self.presets_dir):
            return []
        
        presets = []
        for file in os.listdir(self.presets_dir):
            if file.endswith('.json'):
                preset_name = file[:-5]  # 移除.json後綴
                presets.append(preset_name)
        return sorted(presets)
    
    def save_preset(self, config_instance, preset_name):
        """保存當前配置為參數配置"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        # 創建預設配置數據 - 確保包含所有重要參數
        preset_data = {
            'name': preset_name,
            'created_time': datetime.now().isoformat(),
            'description': f"參數配置 - {preset_name}",
            'config': {
                # 基本檢測參數
                'fov_size': getattr(config_instance, 'fov_size', 666),
                'min_confidence': getattr(config_instance, 'min_confidence', 0.66),
                'detect_interval': getattr(config_instance, 'detect_interval', 0.006),
                'model_path': getattr(config_instance, 'model_path', os.path.join('模型', 'Rivals.onnx')),
                'model_input_size': getattr(config_instance, 'model_input_size', 640),
                'current_provider': getattr(config_instance, 'current_provider', "CPUExecutionProvider"),
                
                # PID控制器參數
                'pid_kp_x': getattr(config_instance, 'pid_kp_x', 0.26),
                'pid_ki_x': getattr(config_instance, 'pid_ki_x', 0.0),
                'pid_kd_x': getattr(config_instance, 'pid_kd_x', 0.0),
                'pid_kp_y': getattr(config_instance, 'pid_kp_y', 0.26),
                'pid_ki_y': getattr(config_instance, 'pid_ki_y', 0.0),
                'pid_kd_y': getattr(config_instance, 'pid_kd_y', 0.0),
                
                # 瞄準設定
                'aim_part': getattr(config_instance, 'aim_part', 'head'),
                'single_target_mode': getattr(config_instance, 'single_target_mode', True),
                'head_width_ratio': getattr(config_instance, 'head_width_ratio', 0.38),
                'head_height_ratio': getattr(config_instance, 'head_height_ratio', 0.26),
                'body_width_ratio': getattr(config_instance, 'body_width_ratio', 0.87),
                
                # 按鍵設定
                'AimKeys': getattr(config_instance, 'AimKeys', [0x01, 0x06, 0x02]),
                'aim_toggle_key': getattr(config_instance, 'aim_toggle_key', 45),
                'auto_fire_key': getattr(config_instance, 'auto_fire_key', 0x06),
                'auto_fire_key2': getattr(config_instance, 'auto_fire_key2', 0x04),
                
                # 自動開火設定
                'auto_fire_delay': getattr(config_instance, 'auto_fire_delay', 0.0),
                'auto_fire_interval': getattr(config_instance, 'auto_fire_interval', 0.18),
                'auto_fire_target_part': getattr(config_instance, 'auto_fire_target_part', "both"),
                
                # 顯示設定
                'show_confidence': getattr(config_instance, 'show_confidence', True),
                'show_fov': getattr(config_instance, 'show_fov', True),
                'show_boxes': getattr(config_instance, 'show_boxes', True),
                'show_status_panel': getattr(config_instance, 'show_status_panel', True),
                
                # 功能開關
                'AimToggle': getattr(config_instance, 'AimToggle', True),
                'keep_detecting': getattr(config_instance, 'keep_detecting', True),
                'fov_follow_mouse': getattr(config_instance, 'fov_follow_mouse', False),

                
                # 性能設定
                'performance_mode': getattr(config_instance, 'performance_mode', True),
                'max_queue_size': getattr(config_instance, 'max_queue_size', 1),
                
                # CPU性能優化參數
                'cpu_optimization': getattr(config_instance, 'cpu_optimization', True),
                'thread_priority': getattr(config_instance, 'thread_priority', 'high'),
                'process_priority': getattr(config_instance, 'process_priority', 'high'),
                'cpu_affinity': getattr(config_instance, 'cpu_affinity', None),
                
                # 音效提示系統
                'enable_sound_alert': getattr(config_instance, 'enable_sound_alert', True),
                'sound_frequency': getattr(config_instance, 'sound_frequency', 1000),
                'sound_duration': getattr(config_instance, 'sound_duration', 100),
                'sound_interval': getattr(config_instance, 'sound_interval', 200),
            }
        }
        
        try:
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存參數配置失敗: {e}")
            return False
    
    def load_preset(self, config_instance, preset_name):
        """載入參數配置"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        if not os.path.exists(preset_path):
            return False
            
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # 載入配置到實例
            config_data = preset_data.get('config', {})
            for key, value in config_data.items():
                if hasattr(config_instance, key):
                    setattr(config_instance, key, value)
            
            return True
        except Exception as e:
            print(f"載入參數配置失敗: {e}")
            return False
    
    def delete_preset(self, preset_name):
        """刪除參數配置"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        if os.path.exists(preset_path):
            try:
                os.remove(preset_path)
                return True
            except Exception as e:
                print(f"刪除參數配置失敗: {e}")
                return False
        return False
    
    def rename_preset(self, old_name, new_name):
        """重命名參數配置"""
        old_path = os.path.join(self.presets_dir, f"{old_name}.json")
        new_path = os.path.join(self.presets_dir, f"{new_name}.json")
        
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                # 讀取舊文件並更新名稱
                with open(old_path, 'r', encoding='utf-8') as f:
                    preset_data = json.load(f)
                preset_data['name'] = new_name
                
                # 寫入新文件
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(preset_data, f, ensure_ascii=False, indent=2)
                
                # 刪除舊文件
                os.remove(old_path)
                return True
            except Exception as e:
                print(f"重命名參數配置失敗: {e}")
                return False
        return False
    
    def export_preset(self, preset_name, export_path):
        """匯出參數配置"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        if os.path.exists(preset_path):
            try:
                shutil.copy2(preset_path, export_path)
                return True
            except Exception as e:
                print(f"匯出參數配置失敗: {e}")
                return False
        return False
    
    def import_preset(self, import_path):
        """匯入參數配置"""
        if not os.path.exists(import_path):
            return False
            
        try:
            # 讀取匯入的配置
            with open(import_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # 獲取配置名稱
            preset_name = preset_data.get('name', 'imported_preset')
            
            # 確保名稱唯一
            original_name = preset_name
            counter = 1
            while os.path.exists(os.path.join(self.presets_dir, f"{preset_name}.json")):
                preset_name = f"{original_name}_{counter}"
                counter += 1
            
            # 更新名稱並保存
            preset_data['name'] = preset_name
            preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
            
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)
            
            return preset_name
        except Exception as e:
            print(f"匯入參數配置失敗: {e}")
            return False


class PresetManagerGUI:
    def __init__(self, parent, config_instance, update_callback=None):
        self.config = config_instance
        self.preset_manager = PresetManager()
        self.update_callback = update_callback
        
        # 創建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("參數管理")
        self.window.geometry("800x600")
        self.window.configure(bg="#250526")
        
        # 防止窗口被調整大小
        self.window.resizable(False, False)
        
        # 設置窗口置中
        self.center_window()
        
        self.setup_ui()
        self.refresh_preset_list()
        
    def center_window(self):
        """將窗口置中顯示"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
    
    def setup_ui(self):
        """設置用戶界面"""
        # 主框架
        main_frame = tk.Frame(self.window, bg="#250526")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 左側：預設列表
        left_frame = tk.Frame(main_frame, bg="#120606", relief="groove", bd=2)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 參數列表標題
        tk.Label(left_frame, text="參數配置", bg="#120606", fg="white", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # 參數列表框架
        list_frame = tk.Frame(left_frame, bg="#120606")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 參數列表
        self.preset_listbox = tk.Listbox(list_frame, bg="#2a0a2a", fg="white", 
                                        selectbackground="#4a2a4a", 
                                        selectforeground="white",
                                        font=("Arial", 12),
                                        height=20)
        self.preset_listbox.pack(side="left", fill="both", expand=True)
        
        # 滾動條
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.preset_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.preset_listbox.yview)
        
        # 右側：控制按鈕
        right_frame = tk.Frame(main_frame, bg="#120606", relief="groove", bd=2)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        
        # 標題
        tk.Label(right_frame, text="參數配置", bg="#120606", fg="white", 
                font=("Arial", 14, "bold")).pack(pady=20)
        
        # 當前選中顯示
        self.selected_label = tk.Label(right_frame, text="參數名稱：未選擇", 
                                      bg="#120606", fg="#cccccc", 
                                      font=("Arial", 10))
        self.selected_label.pack(pady=(0, 20))
        
        # 按鈕樣式
        button_style = {
            "bg": "#4a2a4a",
            "fg": "white",
            "activebackground": "#6a4a6a",
            "activeforeground": "white",
            "font": ("Arial", 10, "bold"),
            "width": 15,
            "height": 2,
            "relief": "raised",
            "bd": 2
        }
        
        # 第一行按鈕
        row1_frame = tk.Frame(right_frame, bg="#120606")
        row1_frame.pack(pady=5)
        
        tk.Button(row1_frame, text="創建參數", command=self.create_new_preset, 
                 **button_style).pack(side="left", padx=5)
        tk.Button(row1_frame, text="重命名參數", command=self.rename_preset, 
                 **button_style).pack(side="left", padx=5)
        
        # 第二行按鈕
        row2_frame = tk.Frame(right_frame, bg="#120606")
        row2_frame.pack(pady=5)
        
        tk.Button(row2_frame, text="載入參數", command=self.load_preset, 
                 **button_style).pack(side="left", padx=5)
        tk.Button(row2_frame, text="保存參數", command=self.save_preset, 
                 **button_style).pack(side="left", padx=5)
        
        # 第三行按鈕
        row3_frame = tk.Frame(right_frame, bg="#120606")
        row3_frame.pack(pady=5)
        
        tk.Button(row3_frame, text="刷新列表", command=self.refresh_preset_list, 
                 **button_style).pack(side="left", padx=5)
        tk.Button(row3_frame, text="刪除參數", command=self.delete_preset, 
                 **button_style).pack(side="left", padx=5)
        
        # 第四行按鈕（文件操作）
        row4_frame = tk.Frame(right_frame, bg="#120606")
        row4_frame.pack(pady=20)
        
        tk.Button(row4_frame, text="打開配置文件夾", command=self.open_presets_folder, 
                 bg="#2a4a2a", fg="white", activebackground="#4a6a4a", 
                 font=("Arial", 10, "bold"), width=20, height=2).pack()
        
        # 匯入匯出按鈕
        row5_frame = tk.Frame(right_frame, bg="#120606")
        row5_frame.pack(pady=10)
        
        tk.Button(row5_frame, text="匯入參數", command=self.import_preset, 
                 **button_style).pack(side="left", padx=5)
        tk.Button(row5_frame, text="匯出參數", command=self.export_preset, 
                 **button_style).pack(side="left", padx=5)
        
        # 綁定列表選擇事件
        self.preset_listbox.bind('<<ListboxSelect>>', self.on_preset_select)
    
    def refresh_preset_list(self):
        """刷新參數列表"""
        self.preset_listbox.delete(0, tk.END)
        presets = self.preset_manager.get_preset_list()
        for preset in presets:
            self.preset_listbox.insert(tk.END, preset)
    
    def on_preset_select(self, event):
        """處理參數選擇事件"""
        selection = self.preset_listbox.curselection()
        if selection:
            preset_name = self.preset_listbox.get(selection[0])
            self.selected_label.config(text=f"參數名稱：{preset_name}")
    
    def get_selected_preset(self):
        """獲取當前選中的參數"""
        selection = self.preset_listbox.curselection()
        if selection:
            return self.preset_listbox.get(selection[0])
        return None
    
    def create_new_preset(self):
        """創建新參數"""
        name = simpledialog.askstring("新建參數", "請輸入參數名稱:")
        if name:
            if self.preset_manager.save_preset(self.config, name):
                messagebox.showinfo("成功", f"參數 '{name}' 創建成功!")
                self.refresh_preset_list()
            else:
                messagebox.showerror("錯誤", "創建參數失敗!")
    
    def rename_preset(self):
        """重命名參數"""
        old_name = self.get_selected_preset()
        if not old_name:
            messagebox.showwarning("警告", "請先選擇一個參數!")
            return
        
        new_name = simpledialog.askstring("重命名參數", f"重命名 '{old_name}' 為:", initialvalue=old_name)
        if new_name and new_name != old_name:
            if self.preset_manager.rename_preset(old_name, new_name):
                messagebox.showinfo("成功", f"參數重命名為 '{new_name}' 成功!")
                self.refresh_preset_list()
            else:
                messagebox.showerror("錯誤", "重命名參數失敗!")
    
    def load_preset(self):
        """載入參數"""
        preset_name = self.get_selected_preset()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個參數!")
            return
        
        if self.preset_manager.load_preset(self.config, preset_name):
            messagebox.showinfo("成功", f"參數 '{preset_name}' 載入成功!")
            if self.update_callback:
                self.update_callback()
        else:
            messagebox.showerror("錯誤", "載入參數失敗!")
    
    def save_preset(self):
        """保存當前配置為參數"""
        preset_name = self.get_selected_preset()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個參數或創建新參數!")
            return
        
        result = messagebox.askyesno("確認", f"確定要用當前配置覆蓋參數 '{preset_name}' 嗎?")
        if result:
            if self.preset_manager.save_preset(self.config, preset_name):
                messagebox.showinfo("成功", f"參數 '{preset_name}' 保存成功!")
            else:
                messagebox.showerror("錯誤", "保存參數失敗!")
    
    def delete_preset(self):
        """刪除參數"""
        preset_name = self.get_selected_preset()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個參數!")
            return
        
        result = messagebox.askyesno("確認刪除", f"確定要刪除參數 '{preset_name}' 嗎?\n此操作無法復原!")
        if result:
            if self.preset_manager.delete_preset(preset_name):
                messagebox.showinfo("成功", f"參數 '{preset_name}' 刪除成功!")
                self.refresh_preset_list()
                self.selected_label.config(text="參數名稱：未選擇")
            else:
                messagebox.showerror("錯誤", "刪除參數失敗!")
    
    def open_presets_folder(self):
        """打開參數文件夾"""
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
    
    def import_preset(self):
        """匯入參數配置"""
        file_path = filedialog.askopenfilename(
            title="選擇要匯入的參數文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            result = self.preset_manager.import_preset(file_path)
            if result:
                messagebox.showinfo("成功", f"參數匯入成功，名稱為: {result}")
                self.refresh_preset_list()
            else:
                messagebox.showerror("錯誤", "匯入參數失敗!")
    
    def export_preset(self):
        """匯出參數配置"""
        preset_name = self.get_selected_preset()
        if not preset_name:
            messagebox.showwarning("警告", "請先選擇一個參數!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="選擇匯出位置",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue=f"{preset_name}.json"
        )
        
        if file_path:
            if self.preset_manager.export_preset(preset_name, file_path):
                messagebox.showinfo("成功", f"參數 '{preset_name}' 匯出成功!")
            else:
                messagebox.showerror("錯誤", "匯出參數失敗!") 