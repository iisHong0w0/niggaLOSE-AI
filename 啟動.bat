@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置颜色
color 0A

echo.
echo ========================================
echo    NiggaLOSE AI 自动环境检测与启动
echo ========================================
echo.

:: 检查Python是否已安装
echo [1/4] 检测Python环境...
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
    echo    1. 请勾选 "Add Python to PATH"
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
echo [2/4] 检测pip工具...
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
echo [3/4] 检测并安装必需的Python包...

:: 定义需要的包列表
set packages=pywin32 tkinter numpy onnxruntime opencv-python mss Pillow

:: 升级pip
echo 📦 正在升级pip...
python -m pip install --upgrade pip

echo.
echo 📦 正在检测和安装依赖包...

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
    ) else (
        python -c "import %%p" >nul 2>&1
        if !errorlevel! neq 0 (
            echo 📥 正在安装 %%p...
            python -m pip install %%p
            if !errorlevel! neq 0 (
                echo ❌ %%p 安装失败
                set install_failed=1
            ) else (
                echo ✅ %%p 安装成功
            )
        ) else (
            echo ✅ %%p 已安装
        )
    )
)

:: 特殊处理：检查是否需要安装pywin32的特殊依赖
echo.
echo 🔧 正在配置pywin32...
python -c "import win32api, win32con, win32gui" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 正在安装pywin32扩展...
    python -m pip install --upgrade pywin32
    python Scripts\pywin32_postinstall.py -install >nul 2>&1
)

echo.
echo [4/4] 验证所有依赖...

:: 验证所有关键模块
set "all_good=1"
for %%m in (win32api win32con win32gui tkinter numpy onnxruntime cv2 mss PIL) do (
    python -c "import %%m" >nul 2>&1
    if !errorlevel! neq 0 (
        echo ❌ %%m 导入失败
        set "all_good=0"
    ) else (
        echo ✅ %%m 验证通过
    )
)

echo.
if "!all_good!"=="1" (
    echo ========================================
    echo ✅ 所有环境检测完成！
    echo ========================================
    echo.
    
    :: 检查主程序文件是否存在
    if exist "NiggaLOSE AI.py" (
        echo 🚀 正在启动 NiggaLOSE AI...
        echo.
        python "NiggaLOSE AI.py"
    ) else (
        echo ❌ 未找到 "NiggaLOSE AI.py" 文件
        echo 📋 请确保以下文件存在于当前目录：
        echo    - NiggaLOSE AI.py
        echo    - rivals.onnx (AI模型文件)
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