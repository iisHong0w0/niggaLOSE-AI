# Axiom-AI v4

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-PolyForm--Noncommercial%201.0.0-blueviolet.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/iishong0w0/Axiom-AI)
![Repo Size](https://img.shields.io/github/repo-size/iishong0w0/Axiom-AI)

A high-performance, Python-based AI gaming assistant featuring a real-time visual overlay and a highly customizable GUI. It supports dual AI engines (ONNX and PyTorch) and offers a seamless out-of-the-box experience through an intelligent installation script.

---

## 🚀 Quick Start

All users should obtain the latest version from the official link below.

### [**>> Download Latest Release <<**](https://github.com/iishong0w0/Axiom-AI/releases/latest)

---

### Control Panel
![Control Panel](https://raw.githubusercontent.com/iisHong0w0/Axiom-AI/refs/heads/main/%E9%9D%A2%E6%9D%BF.png)

### In-Game Demonstration
![In-Game Demo](https://raw.githubusercontent.com/iisHong0w0/Axiom-AI/refs/heads/main/%E5%B1%95%E7%A4%BA.gif)

---
## ✨ Features

*   ⚡ **Intelligent Hardware-Aware Installation**: The built-in `Run Launcher.bat` script automatically installs the necessary AI libraries.
*   🧠 **Dual AI Engine Support**:
    *   **ONNX Runtime**: Full support for GPU acceleration (DirectML for AMD/Intel, CUDA for NVIDIA), providing low-latency object detection.
    *   **PyTorch**: Full support for YOLOv8 (`.pt`) models, capable of leveraging NVIDIA GPU CUDA cores for high-performance computing.
*   📂 **Modular Model Management**: Simply drop new `.onnx` or `.pt` model files into the `models` folder, and the program will dynamically load and allow switching via the GUI without a restart.
*   🖥️ **Graphical User Interface (GUI)**: All parameters such as FOV, aiming speed, confidence threshold, and hotkeys can be adjusted through an intuitive graphical interface.
*   🎨 **Real-time Game Overlay**: A high-performance, low-latency fullscreen overlay built with PyQt6 for drawing detection boxes, confidence scores, and Field of View (FOV).
*   ⚙️ **Highly Customizable**:
    *   Adjustable FOV size
    *   Customizable AI detection confidence threshold
    *   Adjustable aiming speed
    *   **Global Hotkeys**: Toggle the aim assist on/off in-game with a single key press, no Alt-Tabbing required.
    *   Fully customizable mouse and keyboard hotkeys
    *   Switch between "Head" and "Body" aiming modes
    *   Advanced modes like "Hold Detection" and "FOV Follows Mouse"
*   💾 **Automatic Settings Persistence**: All adjusted settings are automatically saved to `config.json` upon exit, eliminating the need for reconfiguration.

---

## 🛠️ Installation & Usage

1.  Go to the [**Releases**](https://github.com/iishong0w0/Axiom-AI/releases/latest) page via the link above.
2.  Download the latest release package (`.zip`).
3.  Extract the package into a new folder.
4.  Place your own AI model files (e.g., `your-model.onnx` or `your-model.pt`) into the `models` folder.
5.  **(First-time use)** If you do not have Python installed, place the official Python installer (e.g., `python-3.13.5-amd64.exe`) in the same folder as `Run Launcher.bat`.
6.  Double-click `Run Launcher.bat`.
7.  The script will **automatically** check your environment and guide you through the installation:
    *   If the Python installer pops up, be sure to check the **`Add Python to PATH`** option during installation. The script will automatically continue after the installation is complete.
8.  Once the setup is finished, the main Axiom-AI program will start automatically.

---

## ⚙️ Control Panel Overview

The new UI layout is divided into six main sections:

*   **Basic Settings**:
    *   **Model**: Dynamically loads all available `.onnx` and `.pt` files from the `models` folder, allowing for real-time switching via a dropdown menu.

*   **Aiming Control**:
    *   **FOV Size**: Adjusts the size of the square detection area.
    *   **Confidence Threshold (%)**: Sets the minimum confidence level required for the AI to register a target.
    *   **Aiming Speed**: Controls how fast the mouse moves to the target. Higher values mean faster/less smooth movement.
    *   **Detection Interval (ms)**: The delay between each AI detection cycle, used to manage performance impact.

*   **Key Settings**:
    *   **Aim Key 1/2/3**: Set up to three different aiming hotkeys.
    *   **Auto-Fire Key**: Sets a key that, when held, will automatically fire when the crosshair is over a detected enemy.
    *   **Toggle Aim Hotkey**: Sets a global hotkey to enable/disable the aim assist at any time.
    *   **Aim Part**: Choose whether the AI should target the enemy's "Head" or "Body".

*   **Auto Functions**:
    *   **Auto-Fire Delay**: The delay (in seconds) before the logic becomes active after pressing the auto-fire key.
    *   **Shooting Interval**: The time interval between automatic shots.
    *   **Anti-Recoil**: Automatically compensates for weapon recoil.

*   **Display Options**:
    *   **Show Confidence**: Toggles the display of the confidence percentage next to the detection box.
    *   **Hold Detection**: If checked, detection boxes will be displayed even if the aim key is not held down.
    *   **FOV Follows Mouse**: If checked, the detection area (FOV) will dynamically follow your mouse cursor.

*   **Program Control**:
    *   **Auto Aim**: Displays the current enabled status (`True`/`False`).
    *   **Inference Device**: Shows the current computing device being used (e.g., DirectML (GPU) or CPU).
    *   **Toggle Auto Aim**: Manually enable or disable the main function from the UI.
    *   **Exit and Save**: Safely closes the program and saves all settings.

---

## 👨‍💻 Developer Information

### Tech Stack
*   **Core**: Python 3.11+
*   **AI Inference**: ONNX Runtime, PyTorch
*   **AI Model Framework**: Ultralytics (YOLOv8)
*   **Settings GUI**: Tkinter
*   **Game Overlay**: PyQt6
*   **Computer Vision**: OpenCV
*   **Screen Capture**: MSS
*   **System Control**: pywin32

### Project Structure
```
/Axiom-AI/
│
├── src/
│   ├── 模型/
│   ├── main.py
│   ├── config.py
│   ├── settings_gui.py
│   ├── overlay.py
│   ├── inference.py
│   ├── win_utils.py
│   ├── language_manager.py
│   └── other module files...
├── 啟動Launcher.bat
├── python-3.13.5-amd64.exe
├── requirements.txt

### Contributing
Contributions in any form are welcome, including bug reports, feature requests, or direct pull requests.

---

## ⚠️ Disclaimer

*   This project is for academic and technical research purposes only.
*   The user is solely responsible for any consequences arising from the use of this project, including but not limited to any form of game account penalties.
*   This project is strictly prohibited for commercial or illegal use.
*   The author is not responsible for any direct or indirect damage caused by the use of this project.
*   This software may violate the terms of service of some games. Use at your own risk.

**By downloading and using this project, you agree to the above terms.**

---

## 📞 Contact

*   **GitHub**: [iishong0w0](https://github.com/iishong0w0)
*   **Email**: iis20160512@gmail.com

---

**Axiom-AI v4 - Made with ❤️**
