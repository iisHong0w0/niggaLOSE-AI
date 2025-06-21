# Axiom-AI

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-PolyForm--Noncommercial%201.0.0-blueviolet.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/iishong0w0/Axiom-AI)
![Repo Size](https://img.shields.io/github/repo-size/iishong0w0/Axiom-AI)

A high-performance, Python-based AI gaming assistant featuring a real-time visual overlay and a highly customizable GUI. It supports dual AI engines (ONNX & PyTorch) and provides an ultimate out-of-the-box experience via an intelligent setup script.

---

### Control Panel
![Control Panel](https://raw.githubusercontent.com/iisHong0w0/Axiom-AI/refs/heads/main/%E9%9D%A2%E6%9D%BF.png)

### In-Game Demonstration
![In-Game Demo](https://raw.githubusercontent.com/iisHong0w0/Axiom-AI/refs/heads/main/%E5%B1%95%E7%A4%BA.gif)

---

## 🚀 Quick Start

All users should obtain the latest version from the official link below.

### [**>> Download the Latest Release <<**](https://github.com/iisHong0w0/Axiom-AI_Aimbot/releases/tag/v1.1)

---

## ✨ Features

*   ⚡ **Intelligent Hardware-Aware Setup**: The included `啟動.bat` (launch.bat) script automatically installs the corresponding optimized AI libraries for a true out-of-the-box experience.
*   🧠 **Dual AI Engine Support**:
    *   **ONNX Runtime**: Full support for GPU acceleration (DirectML for AMD/Intel, CUDA for NVIDIA), providing low-latency object detection.
    *   **PyTorch**: Full support for YOLOv8 (`.pt`) models, capable of leveraging NVIDIA GPU CUDA cores for high-performance computing.
*   📂 **Modular Model Management**: Simply place your new `.onnx` or `.pt` model files into the `模型` (Models) folder, and the program will dynamically load and switch between them via the GUI, no restart required.
*   🖥️ **Graphical User Interface (GUI)**: All parameters, such as FOV, aiming speed, confidence threshold, and hotkeys, can be adjusted through an intuitive graphical interface.
*   🎨 **Real-time Game Overlay**: A high-performance, low-latency fullscreen overlay built with PyQt6 to draw detection boxes, confidence scores, and the Field of View (FOV).
*   ⚙️ **Highly Customizable**:
    *   Adjustable FOV size.
    *   Customizable AI detection confidence threshold.
    *   Tunable aiming speed.
    *   **Global Hotkey**: Toggle the aim assist on/off from within the game with a single key press, no Alt-Tabbing needed.
    *   Fully customizable mouse and keyboard hotkeys.
    *   Switch between "Head" and "Body" targeting modes.
    *   Advanced modes like "Keep Detecting" and "FOV Follows Mouse".
*   💾 **Automatic Settings Persistence**: All adjusted settings are automatically saved to `config.json` upon exit, eliminating the need for reconfiguration.

---

## 🛠️ Installation & Usage

1.  Navigate to the [**Releases**](https://github.com/iishong0w0/Axiom-AI_Aimbot/releases/tag/v1.1) page linked above.
2.  Download the latest release package (`.zip`).
3.  Extract the package to a new folder.
4.  Place your own AI model files (e.g., `your-model.onnx` or `your-model.pt`) into the `模型` (Models) folder.
5.  **(First-Time Use)** If you don't have Python installed, place the official Python installer (e.g., `python-3.13.4.exe`) in the same folder as `啟動.bat`.
6.  Double-click `啟動.bat`.
7.  The script will **automatically** check your environment and guide you through the installation:
    *   **Select Hardware**: Follow the prompts to enter `1` (NVIDIA), `2` (AMD/Intel), or `3` (CPU-only) to install the AI libraries best suited for your computer.
    *   If the Python installer pops up, be sure to check the **`Add Python to PATH`** option during installation. The script will continue automatically after it's done.
8.  Once the setup is complete, the Axiom-AI main program will start automatically.

---

## ⚙️ Control Panel Overview

The new UI layout is divided into three main areas:

*   **Model Settings**:
    *   **Model**: Dynamically loads all available `.onnx` and `.pt` files from the `模型` (Models) folder, allowing for on-the-fly switching via the dropdown menu.

*   **Parameter Tuning**:
    *   **FOV Size**: Adjusts the size of the square detection area.
    *   **Confidence Threshold (%)**: Sets the minimum confidence level required for the AI to register a target.
    *   **Aiming Speed**: Controls how fast the mouse moves to the target. Higher values are faster/less smooth.
    *   **Detection Interval (ms)**: The delay between each AI detection cycle, used to manage performance impact.

*   **Program Control (Misc)**:
    *   **Aim Assist**: Displays the current enabled state (`True`/`False`).
    *   **Inference Device**: Shows the current computing device being used (e.g., DirectML (GPU) or CPU).
    *   **Toggle Aim Assist**: Manually enable or disable the main function from the UI.
    *   **Exit and Save**: Safely closes the program and saves all settings.

*   **Display & Modes (Detection)**:
    *   **Show Confidence**: Toggles the display of the confidence percentage next to detection boxes.
    *   **Keep Detecting**: If checked, detection boxes will be displayed even when the aim key is not held down.
    *   **FOV Follows Mouse**: If checked, the detection area (FOV) will dynamically follow your mouse cursor.

*   **Keybinds & Targeting**:
    *   **Aim Key 1/2**: Click a button and press any key to bind up to two different aim hotkeys.
    *   **Auto-Fire Key**: Set a key that, when held, will automatically fire when the crosshair is on a detected enemy.
    *   **Toggle Aim Hotkey**: Set a global hotkey to enable/disable the aim assist at any time.
    *   **Aiming Part**: Choose whether the AI should target the enemy's "head" or "body".
    *   **Auto-Fire Delay**: The delay in seconds after pressing the auto-fire key before the logic becomes active.

---

## 👨‍💻 For Developers

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
|
├── 模型/               # Stores all .onnx and .pt model files
├── 啟動.bat            # Intelligent installation and launch script
├── main.py             # Main program entry point, handles threading and coordination
├── config.py           # Manages all settings (reads/writes config.json)
├── settings_gui.py     # All code for the Tkinter settings interface
├── overlay.py          # Code for the PyQt6 screen overlay
├── inference.py        # Helper functions for ONNX model inference
├── win_utils.py        # Utility functions for Windows API calls
└── requirements.txt    # List of project dependencies
```

### Contributing
Contributions of all forms are welcome, including bug reports, feature requests, or direct pull requests.

---

## ⚠️ Disclaimer

*   This project is intended for academic and technical research purposes only.
*   The user assumes all responsibility for any consequences arising from the use of this project, including but not limited to any form of game account penalties.
*   Commercial or illegal use of this project is strictly prohibited.
*   The author is not responsible for any direct or indirect damages caused by the use of this project.
*   This software may violate Terms of Service of certain games. Use at your own risk.
**By downloading and using this project, you agree to the above terms.**
