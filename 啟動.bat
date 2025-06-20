@echo off
cd /d "%~dp0"
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置颜色
color 0A

echo.
echo ========================================
echo       Axiom AI 自动环境检测与启动
echo ========================================
echo.

:: ----------------------------------------------------------------------
:: [1/5] 检测Python环境
:: ----------------------------------------------------------------------
echo [1/5] 检测Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo.
    echo 🔍 正在查找Python 3.13.4安装包...
    
    :: 查找Python安装包
    set "python_installer="
    for %%f in (python-3.13.4*.exe) do (
        set "python_installer=%%f"
        goto found_installer
    )
    
    :found_installer
    if "!python_installer!"=="" (
        echo ❌ 未找到Python 3.13.4安装包
        echo 📋 请确保以下文件之一存在于当前目录：
        echo    - python-3.13.4.exe
        echo    - python-3.13.4-amd64.exe
        echo    - python-3.13.4-win32.exe
        echo.
        pause
        exit /b 1
    )
    
    echo ✅ 找到安装包: !python_installer!
    echo 🚀 正在启动Python安装程序...
    echo.
    echo 📋 安装说明：
    echo    1. 请务必勾选 "Add Python to PATH"
    echo    2. 建议选择 "Install Now" 或自定义安装
    echo    3. 安装完成后关闭安装程序窗口
    echo.
    
    start "" "!python_installer!"
    
    echo ⏳ 等待Python安装完成...
    echo 💡 安装完成后请按任意键继续
    pause >nul
    
    :: 重新检查Python
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo ❌ Python安装可能未成功或未添加到PATH
        echo 💡 请重启命令提示符或重新运行此脚本
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%a in ('python --version 2^>^&1') do set python_version=%%a
    echo ✅ !python_version! 已安装
)

echo.
:: ----------------------------------------------------------------------
:: [2/5] 检测pip工具并升级
:: ----------------------------------------------------------------------
echo [2/5] 检测pip工具...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip未安装，正在尝试安装...
    python -m ensurepip --upgrade
    if !errorlevel! neq 0 (
        echo ❌ pip安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ pip已安装
)

echo.
:: ----------------------------------------------------------------------
:: [3/5] 检测并安装必需的Python包
:: ----------------------------------------------------------------------
echo [3/5] 检测并安装必需的Python包...

:: **=== 修改點 1：加入了 PyQt6 ===**
set packages=PyQt6 pywin32 tkinter numpy opencv-python mss Pillow

:: 升级pip
echo 📦 正在升级pip...
python -m pip install --upgrade pip >nul 2>&1

echo.
echo 🚀 正在配置AI核心以啟用GPU加速 (DirectML)...
:: 1. 首先，卸载可能存在的任何onnxruntime版本，以避免冲突
echo    - 正在清理舊版本...
python -m pip uninstall -y onnxruntime onnxruntime-gpu onnxruntime-directml >nul 2>&1
:: 2. 强制安装DirectML版本
echo    - 正在安裝DirectML版本...
python -m pip install onnxruntime-directml
if !errorlevel! neq 0 (
    echo ❌ DirectML AI核心安裝失敗！請檢查網路。
    pause
    exit /b 1
) else (
    echo ✅ DirectML AI核心配置成功！
)


echo.
echo 📦 正在检测和安装其余依赖包...
for %%p in (%packages%) do (
    echo 检测 %%p...
    
    if "%%p"=="tkinter" (
        :: tkinter通常随Python一起安装，特殊检查
        python -c "import tkinter" >nul 2>&1
        if !errorlevel! neq 0 (
            echo ⚠️  tkinter未找到，这通常随Python安装，可能需要重新安装Python
        ) else (
            echo ✅ tkinter 已安装
        )
    ) else {
        python -c "import %%p" >nul 2>&1
        if !errorlevel! neq 0 (
            echo 📥 正在安装 %%p...
            python -m pip install %%p
            if !errorlevel! neq 0 (
                echo ❌ %%p 安装失败
            ) else {
                echo ✅ %%p 安装成功
            }
        ) else (
            echo ✅ %%p 已安装
        )
    }
)

:: 特殊处理：检查是否需要安装pywin32的特殊依赖
echo.
echo 🔧 正在配置pywin32...
python -c "import win32api" >nul 2>&1
if %errorlevel! neq 0 (
    echo 📥 正在运行pywin32扩展脚本...
    python Scripts\pywin32_postinstall.py -install >nul 2>&1
)

echo.
:: ----------------------------------------------------------------------
:: [4/5] 验证所有依赖
:: ----------------------------------------------------------------------
echo [4/5] 验证所有依赖...

:: **=== 修改點 2：加入了 PyQt6 到验证列表 ===**
set "all_good=1"
for %%m in (PyQt6 win32api win32con win32gui tkinter numpy onnxruntime cv2 mss PIL) do (
    python -c "import %%m" >nul 2>&1
    if !errorlevel! neq 0 (
        echo ❌ 模块 %%m 导入失败
        set "all_good=0"
    ) else (
        echo ✅ 模块 %%m 验证通过
    )
)

echo.
if "!all_good!"=="1" (
    echo ========================================
    echo ✅ 所有环境检测完成！
    echo ========================================
    echo.
    
    :: **=== 修改點 3：更新啟動檔案名稱 ===**
    if exist "Axiom.py" (
        echo 🚀 正在启动 Axiom AI...
        echo.
        python "Axiom.py"
    ) else (
        echo ❌ 未找到 "Axiom.py" 文件
        echo 📋 请确保以下文件存在于当前目录：
        echo    - Axiom.py
        echo    - Rivals.onnx (AI模型文件)
        echo    - logo.png (可选，程序图标)
        echo.
    )
) else (
    echo ========================================
    echo ❌ 环境配置未完成
    echo ========================================
    echo.
    echo 💡 建议操作：
    echo    1. 检查网络连接
    echo    2. 以管理员身份运行此脚本
    echo    3. 手动安装失败的包：
    echo       python -m pip install [包名]
    echo.
)

echo.
echo 按任意键退出...
pause >nul