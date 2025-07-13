# language_manager.py
import json
import os

class LanguageManager:
    def __init__(self):
        self.current_language = "zh_tw"  # 預設繁體中文
        self.translations = {
            "zh_tw": {
                # 視窗標題
                "window_title": "Axiom V4_h0pZ_iis20160512@gmail.com",
                
                # 模型設定
                "model_settings": "模型設定",
                "model": "模型:",
                
                # 通用參數
                "general_params": "通用參數",
                "fov_size": "FOV大小",
                "min_confidence": "檢測最低概率(%)",
                "detect_interval": "檢測間隔(ms)",
                "single_target_mode": "單目標模式 (一次最多鎖定一個最近的敵人)",
                
                # PID 控制
                "aim_speed_pid": "瞄準速度 (PID)",
                "horizontal_x": "水平 (X軸)",
                "vertical_y": "垂直 (Y軸)",
                "reaction_speed_p": "反應速度 (P)",
                "error_correction_i": "誤差修正 (I)",
                "stability_suppression_d": "穩定抑制 (D)",
                
                # 程式控制
                "program_control": "程式控制",
                "auto_aim": "自動瞄準",
                "compute_mode": "運算模式",
                "cpu": "CPU",
                "gpu_directml": "DirectML (GPU)",
                "gpu_cuda": "CUDA (GPU)",
                "toggle_auto_aim": "自動瞄準開關",
                "exit_and_save": "退出並保存",
                
                # 功能選項
                "function_options": "功能選項",
                "show_confidence": "顯示檢測概率",
                "show_fov": "顯示FOV",
                "show_boxes": "顯示人物框",
                "keep_detecting": "保持檢測 (即使未按瞄準鍵)",
                "fov_follow_mouse": "FOV跟隨鼠標",

                
                # ***** 新增：音效提示系統 *****
                "sound_alert_system": "音效提示系統",
                "enable_sound_alert": "啟用音效提示 (準心在敵人框內時)",
                "sound_frequency": "音效頻率 (Hz)",
                "sound_duration": "音效持續時間 (ms)",
                "sound_interval": "音效間隔 (ms)",
                
                # 按鍵與自動開火
                "keys_and_auto_fire": "按鍵與自動開火",
                "aim_key_1": "瞄準按鍵 1:",
                "aim_key_2": "瞄準按鍵 2:",
                "aim_key_3": "瞄準按鍵 3:",
                "auto_fire_key_1": "自動開槍鍵 1:",
                "auto_fire_key_2": "自動開槍鍵 2:",
                "toggle_key": "總開關鍵:",
                "aim_part": "瞄準部位:",
                "auto_fire_target": "自動射擊目標:",
                "scope_delay": "開鏡延遲(s)",
                "fire_interval": "射擊間隔(s)",
                "head": "頭部",
                "body": "身體",
                "both": "兩者",
                
                # 區域占比設定
                "target_area_settings": "目標區域設定",
                "head_width_ratio": "頭部寬度占比 (%)",
                "head_height_ratio": "頭部高度占比 (%)",
                "body_width_ratio": "身體寬度占比 (%)",
                
                # 分頁標題
                "tab_basic": "基本設定",
                "tab_aim_control": "瞄準控制",
                "tab_keys": "按鍵設定",
                "tab_auto_features": "自動功能",
                "tab_display": "顯示選項",
                "tab_program_control": "程式控制",
                "tab_preset_management": "參數管理",
                
                # 關於視窗
                "about": "關於",
                "about_title": "關於 Axiom V4",
                "about_subtitle": "高性能 AI 瞄準輔助工具",
                "i_am_human": "我是人類",
                "join_discord": "加入 Discord",
                "view_github": "查看 GitHub",
                "version_info": "Version 4.0 - Made with ❤️",
                "close": "關閉",
                
                # 按鍵監聽
                "key_listening": "[按鍵...]",
                
                # 狀態面板
                "status_panel_on": "開啟",
                "status_panel_off": "關閉",
                "status_panel_compute_mode": "運算模式",
                "status_panel_current_model": "當前模型",
                
                # 語言切換
                "language": "語言",
                "chinese": "中文",
                "english": "English",
                # 捐款
                "donate": "捐款",
                "donate_en": "Donate",
                
                # 高級/簡單模式切換
                "advanced_mode": "高級模式",
                "simple_mode": "簡單模式",
                "mode_switch_tooltip": "切換高級/簡單模式\n高級模式：完整功能\n簡單模式：簡化操作",
                "unified_xy_speed": "統一 X/Y 軸速度",
                "unified_speed_tooltip": "同時調整水平和垂直軸的瞄準速度",
                
                # 設定檔相關
                "config_saved": "設定已儲存",
                "config_loaded": "設定檔已載入",
                "config_not_found": "未找到設定檔，使用預設值",
                "config_load_failed": "設定載入失敗",
                "config_save_failed": "設定儲存失敗",
                
                # 縮放警告對話框
                "scaling_warning_title": "⚠️ 系統設定問題",
                "scaling_warning_main_title": "⚠️ 檢測到 Windows 縮放設定問題",
                "scaling_current_setting": "當前 Windows 縮放比例: {}%",
                "scaling_explanation": "此程序需要 Windows 縮放比例設定為 100% 才能正常運作\n否則瞄準位置會出現偏移問題",
                "scaling_tutorial_title": "📋 修改步驟:",
                "scaling_tutorial_content": """1. 在桌面上右鍵點擊，選擇「顯示設定」

2. 或者按 Windows鍵 + I，進入「設定」→「系統」→「顯示器」

3. 找到「縮放與版面配置」區域

4. 將「變更文字、應用程式與其他項目的大小」設定為 100%

5. 如果有多個顯示器，請確保所有顯示器都設定為 100%

6. 設定完成後，可能需要重新啟動或登出再登入

7. 完成後重新啟動此程序即可正常使用

💡 提示：
- 如果 100% 太小，建議使用較大解析度的顯示器
- 設定完成後可能需要調整其他軟體的視窗大小
- 這是為了確保程序的準確性和最佳效能""",
                "scaling_close_button": "我知道了，關閉程序",
                
                # ***** 新增：參數管理系統 *****
                "preset_manager": "參數管理",
                "preset_config": "參數配置",
                "parameter_name": "參數名稱",
                "no_selection": "未選中",
                "create_preset": "新建參數",
                "rename_preset": "重新命名", 
                "load_preset": "載入參數",
                "save_preset": "保存參數",
                "refresh_preset": "刷新參數",
                "delete_preset": "刪除參數",
                "open_preset_folder": "打開參數文件夾",
                "import_preset": "匯入參數",
                "export_preset": "匯出參數",
                "preset_success": "成功",
                "preset_error": "錯誤",
                "preset_warning": "警告",
                "confirm_delete": "確認刪除",
                "confirm_overwrite": "確認覆蓋",
                "preset_management_features": "參數管理功能",
                "open_preset_manager": "打開參數管理器",
            },
            
            "en": {
                # Window title
                "window_title": "Axiom V4_h0pZ_iis20160512@gmail.com",
                
                # Model settings
                "model_settings": "Model Settings",
                "model": "Model:",
                # Donate
                "donate": "Donate",
                "donate_en": "Donate",
                
                # General parameters
                "general_params": "General Parameters",
                "fov_size": "FOV Size",
                "min_confidence": "Min Confidence (%)",
                "detect_interval": "Detection Interval (ms)",
                "single_target_mode": "Single Target Mode (Lock on the nearest enemy at a time)",
                
                # PID control
                "aim_speed_pid": "Aim Speed (PID)",
                "horizontal_x": "Horizontal (X-axis)",
                "vertical_y": "Vertical (Y-axis)",
                "reaction_speed_p": "Reaction Speed (P)",
                "error_correction_i": "Error Correction (I)",
                "stability_suppression_d": "Stability Control (D)",
                
                # Program control
                "program_control": "Program Control",
                "auto_aim": "Auto Aim",
                "compute_mode": "Compute Mode",
                "cpu": "CPU",
                "gpu_directml": "DirectML (GPU)",
                "gpu_cuda": "CUDA (GPU)",
                "toggle_auto_aim": "Toggle Auto Aim",
                "exit_and_save": "Exit & Save",
                
                # Function options
                "function_options": "Function Options",
                "show_confidence": "Show Detection Confidence",
                "show_fov": "Show FOV",
                "show_boxes": "Show Player Boxes",
                "keep_detecting": "Keep Detecting (Even Without Aim Key)",
                "fov_follow_mouse": "FOV Follow Mouse",

                
                # ***** 新增：音效提示系統 *****
                "sound_alert_system": "Sound Alert System",
                "enable_sound_alert": "Enable Sound Alert (When Aiming at Enemy)",
                "sound_frequency": "Sound Frequency (Hz)",
                "sound_duration": "Sound Duration (ms)",
                "sound_interval": "Sound Interval (ms)",
                
                # Keys and auto fire
                "keys_and_auto_fire": "Keys & Auto Fire",
                "aim_key_1": "Aim Key 1:",
                "aim_key_2": "Aim Key 2:",
                "aim_key_3": "Aim Key 3:",
                "auto_fire_key_1": "Auto Fire Key 1:",
                "auto_fire_key_2": "Auto Fire Key 2:",
                "toggle_key": "Toggle Key:",
                "aim_part": "Aim Part:",
                "auto_fire_target": "Auto Fire Target:",
                "scope_delay": "Scope Delay (s)",
                "fire_interval": "Fire Interval (s)",
                "head": "Head",
                "body": "Body",
                "both": "Both",
                
                # Target area settings
                "target_area_settings": "Target Area Settings",
                "head_width_ratio": "Head Width Ratio (%)",
                "head_height_ratio": "Head Height Ratio (%)",
                "body_width_ratio": "Body Width Ratio (%)",
                
                # Tab titles
                "tab_basic": "Basic Settings",
                "tab_aim_control": "Aim Control",
                "tab_keys": "Key Settings",
                "tab_auto_features": "Auto Features",
                "tab_display": "Display Options",
                "tab_program_control": "Program Control",
                "tab_preset_management": "Preset Management",
                
                # About window
                "about": "About",
                "about_title": "About Axiom V4",
                "about_subtitle": "High-Performance AI Aim Assistant",
                "i_am_human": "I am Human",
                "join_discord": "Join Discord",
                "view_github": "View GitHub",
                "version_info": "Version 4.0 - Made with ❤️",
                "close": "Close",
                
                # Key listening
                "key_listening": "[Press Key...]",
                
                # Status panel
                "status_panel_on": "ON",
                "status_panel_off": "OFF",
                "status_panel_compute_mode": "Compute Mode",
                "status_panel_current_model": "Current Model",
                
                # Language switch
                "language": "Language",
                "chinese": "中文",
                "english": "English",
                # Donate
                "donate": "Donate",
                "donate_en": "Donate",
                
                # Advanced/Simple mode toggle
                "advanced_mode": "Advanced Mode",
                "simple_mode": "Simple Mode",
                "mode_switch_tooltip": "Toggle Advanced/Simple Mode\nAdvanced: Full features\nSimple: Simplified operation",
                "unified_xy_speed": "Unified X/Y Speed",
                "unified_speed_tooltip": "Adjust horizontal and vertical aim speed together",
                
                # Config related
                "config_saved": "Configuration Saved",
                "config_loaded": "Configuration Loaded",
                "config_not_found": "Configuration file not found, using defaults",
                "config_load_failed": "Failed to load configuration",
                "config_save_failed": "Failed to save configuration",
                
                # Scaling Warning Dialog
                "scaling_warning_title": "⚠️ System Configuration Issue",
                "scaling_warning_main_title": "⚠️ Windows Scaling Configuration Issue Detected",
                "scaling_current_setting": "Current Windows Scaling: {}%",
                "scaling_explanation": "This program requires Windows scaling to be set to 100% to function properly\nOtherwise, aiming positions may be offset",
                "scaling_tutorial_title": "📋 How to Fix:",
                "scaling_tutorial_content": """1. Right-click on desktop and select "Display settings"

2. Or press Windows Key + I, go to "Settings" → "System" → "Display"

3. Find the "Scale and layout" section

4. Set "Change the size of text, apps, and other items" to 100%

5. If you have multiple monitors, ensure all are set to 100%

6. You may need to restart or log out and back in after making changes

7. Restart this program after completion to use normally

💡 Tips:
- If 100% is too small, consider using a higher resolution monitor
- You may need to adjust other software window sizes after setting
- This ensures program accuracy and optimal performance""",
                "scaling_close_button": "Understood, Close Program",
                
                # ***** 新增：配置預設管理系統 *****
                "preset_manager": "Preset Manager",
                "preset_config": "Preset Configuration",
                "parameter_name": "Parameter Name",
                "no_selection": "No Selection",
                "create_preset": "Create Preset",
                "rename_preset": "Rename Preset", 
                "load_preset": "Load Preset",
                "save_preset": "Save Preset",
                "refresh_preset": "Refresh Preset",
                "delete_preset": "Delete Preset",
                "open_preset_folder": "Open Preset Folder",
                "import_preset": "Import Preset",
                "export_preset": "Export Preset",
                "preset_success": "Success",
                "preset_error": "Error",
                "preset_warning": "Warning",
                "confirm_delete": "Confirm Delete",
                "confirm_overwrite": "Confirm Overwrite",
                "preset_management_features": "Preset Management Features",
                "open_preset_manager": "Open Preset Manager",
            }
        }
        
        # 載入語言設定
        self.load_language_config()

    def get_text(self, key, default=""):
        """獲取當前語言的文字"""
        return self.translations.get(self.current_language, {}).get(key, default or key)

    def set_language(self, language_code):
        """設定語言"""
        if language_code in self.translations:
            self.current_language = language_code
            self.save_language_config()
            return True
        return False

    def get_current_language(self):
        """獲取當前語言"""
        return self.current_language

    def get_available_languages(self):
        """獲取可用語言列表"""
        return list(self.translations.keys())

    def save_language_config(self):
        """儲存語言設定"""
        try:
            config_data = {"language": self.current_language}
            with open('language_config.json', 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"語言設定儲存失敗: {e}")

    def load_language_config(self):
        """載入語言設定"""
        try:
            if os.path.exists('language_config.json'):
                with open('language_config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.current_language = config_data.get('language', 'zh_tw')
        except Exception as e:
            print(f"語言設定載入失敗: {e}")
            self.current_language = 'zh_tw'

# 全域語言管理器實例
language_manager = LanguageManager()

def get_text(key, default=""):
    """便捷函數：獲取文字"""
    return language_manager.get_text(key, default)

def set_language(language_code):
    """便捷函數：設定語言"""
    return language_manager.set_language(language_code)