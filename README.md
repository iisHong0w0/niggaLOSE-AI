# Axiom-AI

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-PolyForm--Noncommercial%201.0.0-blueviolet.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/iishong0w0/Axiom-AI)

A high-performance AI-powered gaming assistant built with Python and ONNX, featuring a real-time visual overlay and a highly customizable GUI.

---

### Control Panel
![Control Panel](https://raw.githubusercontent.com/iisHong0w0/Axiom-AI/refs/heads/main/%E9%9D%A2%E6%9D%BF.png)

### In-Game Demonstration
![In-Game Demo](https://raw.githubusercontent.com/iisHong0w0/Axiom-AI/refs/heads/main/%E5%B1%95%E7%A4%BA.gif)

---

## 🚀 Quick Start

**All users should obtain the latest version from the official link below.**

### [**>> Download the Latest Release <<**](https://github.com/iisHong0w0/Axiom-AI/releases/tag/v1.0)

---

## ✨ Features

*   🎮 **High-Performance AI Detection**: Utilizes ONNX Runtime with full support for GPU (DirectML) acceleration for low-latency object detection.
*   🖥️ **Graphical User Interface**: All parameters, such as FOV, aiming speed, and hotkeys, can be adjusted through an intuitive GUI panel.
*   🎨 **Real-time Game Overlay**: A high-performance, low-latency fullscreen overlay built with PyQt6 to draw detection boxes, confidence scores, and the Field of View (FOV).
*   ⚙️ **Highly Customizable**:
    *   Adjustable FOV size and center position.
    *   Configurable AI detection confidence threshold.
    *   Tunable aiming speed and smoothness.
    *   Customizable hotkeys for both mouse and keyboard.
    *   Toggle between "Head" and "Body" aiming modes.
*   ⚡ **One-Click Environment Setup**: The included `啟動.bat` (launch.bat) script automatically detects and installs Python and all necessary dependencies for a true out-of-the-box experience.
*   💾 **Automatic Settings Persistence**: All adjusted settings are automatically saved to `config.json` upon exit, no need for reconfiguration.

---

## 🛠️ Installation & Usage

1.  Navigate to the [**Releases**](https://github.com/iishong0w0/Axiom-AI/releases) page linked above.
2.  Download the latest release package (`.zip`).
3.  Extract the package to a new folder.
4.  **(First-Time Use)** If you don't have Python installed, place the official Python installer (e.g., `python-3.13.4.exe`) in the same folder as `啟動.bat`.
5.  Double-click `啟動.bat`.
6.  The script will **automatically** check your environment and install all required packages.
    *   If the Python installer pops up, make sure to check the **`Add Python to PATH`** option during installation. After it's done, please re-run the `啟動.bat` script.
7.  Once setup is complete, the Axiom-AI main program will start automatically.

---

## ⚙️ Control Panel Overview

*   **Main Control**:
    *   **Toggle Aim Assist**: Enable or disable the AI aiming functionality.
    *   **Inference Device**: Shows the current computing device (GPU or CPU).
*   **Parameter Tuning**:
    *   **FOV Offset X/Y**: Fine-tune the center point of the FOV box.
    *   **FOV Size**: Adjust the size of the square detection area.
    *   **Confidence Threshold (%)**: Sets the minimum confidence level for the AI to display a target.
    *   **Aiming Speed**: Controls how fast the mouse moves to the target. Higher values are faster/less smooth.
    *   **Detection Interval (ms)**: The delay between each AI detection cycle, used to manage performance impact.
*   **Display & Hotkeys**:
    *   **Aim Hotkeys**: Click a button and press any key to bind up to two different aim keys.
    *   **Auto-Fire Hotkey**: Set a key that, when held, will automatically fire when the crosshair is on a detected enemy.
    *   **Auto-Fire Delay**: The delay in seconds after pressing the auto-fire key before the logic becomes active.
    *   **Aiming Part**: Choose whether the AI should target the enemy's head or body.

---

## 👨‍💻 For Developers

### Tech Stack
*   **Core**: Python 3.11+
*   **AI Inference**: ONNX Runtime
*   **Settings GUI**: Tkinter
*   **Game Overlay**: PyQt6
*   **Computer Vision**: OpenCV
*   **Screen Capture**: MSS
*   **System Control**: pywin32

### Contributing
Contributions of all kinds are welcome, including bug reports, feature requests, or direct pull requests.

---

## ⚠️ Disclaimer

*   This project is intended for academic and technical research purposes only.
*   The user assumes all responsibility for any consequences arising from the use of this project, including but not limited to any form of game account penalties.
*   Commercial or illegal use of this project is strictly prohibited.
*   The author is not responsible for any direct or indirect damages caused by the use of this project.

**By downloading and using this project, you agree to the above terms.**
