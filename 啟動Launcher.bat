@echo off
:: ======================================================================
:: Axiom AI - 环境配置与启动脚本
:: ======================================================================

:: --- 初始化环境 ---
cd /d "%~dp0"
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Axiom AI - 环境配置

:START
cls
echo.
echo  ================================================================
echo                    Axiom AI 自动环境检测与启动
echo  ================================================================
echo.
echo  此脚本将自动检测并安装运行所需的环境。
echo.

:: ======================================================================
:: [1/5] 检测Python环境
:: ======================================================================
echo.
echo  [1/5] 检测Python环境...
echo ----------------------------------------------------------------

:: 改进的Python检测方式
python --version >nul 2>&1
set "python_check_result=%errorlevel%"

if %python_check_result% neq 0 (
    echo  ❌ 错误: Python未安装或未添加到系统PATH。
    echo.
    echo  🔍 正在当前目录查找Python安装包...
    
    :: 修正的文件搜索逻辑 - 更新为3.13.5版本
    set "python_installer="
    if exist "python-3.13.5*.exe" (
        for %%f in (python-3.13.5*.exe) do (
            set "python_installer=%%f"
            goto :FOUND_INSTALLER
        )
    )
    
    :FOUND_INSTALLER
    if "!python_installer!"=="" (
        echo  ❌ 错误: 未找到Python 3.13.5安装包。
        echo  📋 请确保 python-3.13.5-amd64.exe 存在于当前目录。
        echo  💡 或者手动安装Python并确保勾选 "Add to PATH"。
        goto :END_ERROR
    )
    
    echo  ✅ 成功: 找到安装包 "!python_installer!"
    echo.
    echo  🚀 即将启动Python安装程序。
    echo.
    echo  📋 安装说明 ^(非常重要!^):
    echo     1. 在安装界面的最下方, 必须勾选 [Add Python.exe to PATH]
    echo     2. 然后点击 [Install Now] 进行默认安装。
    echo     3. 安装完成后, 关闭安装程序窗口, 然后在此处按任意键继续。
    echo.
    pause
    
    start /wait "" "!python_installer!"
    
    echo  ⏳ 正在重新检测Python...
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo  ❌ 错误: Python安装失败或未添加到PATH。
        echo  💡 请重启此脚本, 或手动安装Python并确保勾选 "Add to PATH"。
        goto :END_ERROR
    )
)

:: 获取Python版本信息
for /f "tokens=*" %%a in ('python --version 2^>^&1') do set "python_version=%%a"
echo  ✅ 成功: !python_version! 已安装。
echo.

:: ======================================================================
:: [2/5] 升级pip
:: ======================================================================
echo.
echo  [2/5] 升级pip包管理器...
echo ----------------------------------------------------------------
echo  正在升级pip...
python -m pip install --upgrade pip
if !errorlevel! neq 0 (
    echo  ⚠️  警告: pip升级失败，但将继续安装。
) else (
    echo  ✅ 成功: pip已是最新版本。
)
echo.

:: ======================================================================
:: [3/5] 安装AI核心依赖 - 强制使用DirectML
:: ======================================================================
echo.
echo  [3/5] 配置AI核心依赖 ^(DirectML加速^)...
echo ----------------------------------------------------------------
echo  🚀 正在安装 ONNX Runtime ^(DirectML^) 和 PyTorch ^(CPU^)...
echo     DirectML 支持 NVIDIA/AMD/Intel 所有显卡类型的硬件加速
echo     此过程可能需要一些时间, 请耐心等待。
echo.

:: 先卸载可能存在的其他版本
echo  清理可能存在的 ONNX Runtime 版本...
python -m pip uninstall -y onnxruntime onnxruntime-gpu onnxruntime-directml >nul 2>&1

:: 安装DirectML版本的ONNX Runtime
echo  安装 ONNX Runtime ^(DirectML^)...
python -m pip install onnxruntime-directml
if !errorlevel! neq 0 (
    echo  ❌ 错误: ONNX Runtime ^(DirectML^) 安装失败。
    goto :END_ERROR
)

:: 安装CPU版本的PyTorch
echo  安装 PyTorch ^(CPU^)...
python -m pip install torch torchvision torchaudio
if !errorlevel! neq 0 (
    echo  ❌ 错误: PyTorch ^(CPU^) 安装失败。
    goto :END_ERROR
)

echo  ✅ 成功: DirectML 核心配置完成。

:INSTALL_COMMON
echo  ✅ 成功: AI核心配置完成。
echo.
echo  📦 正在安装其余通用依赖包...

:: 逐个安装包以便更好地错误处理
set "packages=ultralytics PyQt6 pywin32 opencv-python mss Pillow numpy"
for %%p in (%packages%) do (
    echo  安装 %%p...
    python -m pip install %%p
    if !errorlevel! neq 0 (
        echo  ❌ 错误: %%p 安装失败。
        goto :END_ERROR
    )
)

echo  ✅ 成功: 所有通用依赖包安装完成。
echo.

:: 配置pywin32扩展
echo  🔧 正在配置pywin32扩展...
python -c "import sys; import os; sys.path.append(os.path.join(sys.prefix, 'Scripts')); import pywin32_postinstall; pywin32_postinstall.install()" >nul 2>&1
if !errorlevel! neq 0 (
    echo  ⚠️  警告: pywin32配置可能失败，但将继续。
) else (
    echo  ✅ 成功: pywin32配置完成。
)
echo.

:: ======================================================================
:: [4/5] 最终验证
:: ======================================================================
echo.
echo  [4/5] 最终验证所有依赖...
echo ----------------------------------------------------------------
set "all_good=1"

:: 验证关键模块
set "modules=torch ultralytics onnxruntime cv2 PIL PyQt6 win32api numpy"
for %%m in (%modules%) do (
    echo   - 验证模块: %%m
    python -c "import %%m" >nul 2>&1
    if !errorlevel! neq 0 (
        echo     ❌ 失败
        set "all_good=0"
    ) else (
        echo     ✅ 通过
    )
)
echo.

:: ======================================================================
:: [5/5] 启动程序
:: ======================================================================
if "!all_good!"=="1" (
    echo.
    echo  ================================================================
    echo                      ✅ 环境配置完成 ✅
    echo  ================================================================
    echo.
    
    :: 修正程序路径 - 检查src目录下的main.py
    if exist "src\main.py" (
        echo  🚀 正在启动 Axiom AI...
        echo.
        title Axiom AI - 正在运行
        :: 切换到src目录并运行程序，确保程序能正确找到相关模块和配置文件
        cd /d "%~dp0\src"
        python "main.py"
        if !errorlevel! neq 0 (
            echo.
            echo  ❌ 程序运行时出现错误。
            cd /d "%~dp0"
            goto :END_ERROR
        )
        :: 程序结束后返回原目录
        cd /d "%~dp0"
    ) else (
        echo  ❌ 错误: 未找到主程序 "src\main.py"。
        echo  💡 请确保 main.py 文件存在于 src 目录中。
        goto :END_ERROR
    )
) else (
    echo.
    echo  ================================================================
    echo                      ❌ 环境配置失败 ❌
    echo  ================================================================
    echo.
    echo  💡 建议操作：
    echo     1. 检查您的网络连接。
    echo     2. 尝试以 "管理员身份" 重新运行此脚本。
    echo     3. 手动安装失败的包, 例如: python -m pip install [包名]
    echo     4. 检查Python版本是否兼容 ^(建议Python 3.8-3.11^)
    goto :END_ERROR
)

goto :END_SUCCESS

:END_ERROR
echo.
echo  按任意键退出...
pause >nul
exit /b 1

:END_SUCCESS
echo.
echo  程序已退出。按任意键关闭此窗口...
pause >nul
exit /b 0