# WhisperIT Setup & Quick Start Guide

## 🚀 Quick Start (2 minutes)

### macOS & Linux Users

```bash
# Navigate to project directory
cd /Users/andreas.gerhardsson/Sites/WhisperIT

# Run the quick-start script
chmod +x run.sh
./run.sh
```

This will:
1. Create a Python virtual environment if needed
2. Install all dependencies
3. Launch the WhisperIT application

### Windows Users

```cmd
# Navigate to project directory
cd C:\path\to\WhisperIT

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/gui.py
```

---

## 📋 Manual Step-by-Step Setup

If you prefer to set up manually or the quick-start script doesn't work:

### Step 1: Create Virtual Environment

```bash
cd /Users/andreas.gerhardsson/Sites/WhisperIT
python3 -m venv venv
```

**What this does:** Creates an isolated Python environment just for this project. Prevents conflicts with other Python packages on your system.

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

**On Windows:**
```cmd
venv\Scripts\activate
```

You'll see `(venv)` at the start of your terminal prompt when active.

### Step 3: Verify Python & Pip

```bash
python --version    # Should be 3.8+
pip --version       # Should match Python version
```

### Step 4: Upgrade Pip (Important!)

```bash
pip install --upgrade pip
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `openai-whisper` - The transcription engine
- `PySimpleGUI` - GUI framework
- `pydub` - Audio utilities
- Supporting libraries

**Installation takes 2-5 minutes.** On first transcription, Whisper will download the model (~140MB-3GB depending on model selection).

### Step 6: Run the Application

```bash
python src/gui.py
```

A GUI window will open. You're ready to transcribe!

---

## 🔍 Verifying Installation

After installation, verify everything works:

```bash
# Test imports
python -c "import whisper; print(whisper.__version__)"
python -c "import PySimpleGUI as sg; print(sg.version)"

# Should output version numbers without errors
```

If you see errors, check:
1. Virtual environment is activated (`(venv)` in prompt)
2. All requirements installed: `pip list | grep whisper`
3. Python version is 3.8+: `python --version`

---

## ⚙️ First Run Setup

On your first transcription:

1. **Model Download** - Whisper will download the selected model (one-time, ~140MB-3GB)
   - This is automatic and may take 5-15 minutes
   - Requires internet connection
   - Models are cached in `~/.cache/whisper/`

2. **Audio Processing** - PyDub will check for `ffmpeg`
   - If missing, macOS users can install with: `brew install ffmpeg`
   - Linux users: `apt-get install ffmpeg` or `yum install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html or use `choco install ffmpeg`

---

## 📁 Project Structure

```
WhisperIT/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── gui.py                # Main GUI application (start here!)
│   └── transcriber.py        # Transcription logic
├── requirements.txt          # Python dependencies
├── run.sh                    # Quick-start script (macOS/Linux)
├── README.md                 # Full documentation
├── SETUP.md                  # This file
└── .whisperit_config.example # Optional configuration template
```

---

## 🛠️ Troubleshooting

### Virtual Environment Issues

**Problem:** `command not found: python3`
```bash
# Try python instead
python -m venv venv
source venv/bin/activate
```

**Problem:** `(venv)` not showing in prompt
```bash
# Virtual environment might not be activated
source venv/bin/activate  # Activate it
```

**Problem:** Permission denied running `run.sh`
```bash
# Make it executable
chmod +x run.sh
./run.sh
```

### Installation Issues

**Problem:** `pip: command not found`
```bash
# Use python's pip module
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Problem:** `ModuleNotFoundError: No module named 'whisper'`
```bash
# Reinstall requirements
pip install --force-reinstall -r requirements.txt
```

**Problem:** `error: Microsoft Visual C++ 14.0 is required` (Windows)
- Download Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Or install with conda instead: `conda create -n whisper python=3.10 && conda activate whisper`

### Application Issues

**Problem:** GUI doesn't open
```bash
# Try running from terminal to see error messages
python src/gui.py

# If it's a display issue on Linux:
export DISPLAY=:0
python src/gui.py
```

**Problem:** "ffmpeg not found" error
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# Windows - Download from https://ffmpeg.org/download.html
```

**Problem:** Very slow transcription
- This is normal! Processing speed depends on:
  - Audio length (longer = more time)
  - Model size (larger = slower but more accurate)
  - Computer CPU/RAM
  - Use smaller models ('tiny' or 'base') for faster results

---

## 🎯 Next Steps

1. **Read the full documentation:** `README.md`
2. **Try a test transcription** with a short audio file
3. **Explore output formats** to understand what each file contains
4. **Customize settings** as needed for your workflow

---

## 📦 Dependency Details

| Package | Purpose | Size |
|---------|---------|------|
| openai-whisper | Audio transcription | ~200MB |
| PySimpleGUI | GUI framework | ~50KB |
| pydub | Audio file handling | ~200KB |
| tqdm | Progress bars | ~50KB |
| python-dotenv | Config handling | ~20KB |

**Total install size:** ~250MB (plus ~2-3GB for Whisper models)

---

## 🔄 Updating

To update to a newer version of Whisper or other packages:

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## ❌ Uninstalling

To completely remove WhisperIT and its environment:

```bash
cd /Users/andreas.gerhardsson/Sites/WhisperIT
rm -rf venv/
```

This only removes the virtual environment. Your transcriptions and config files remain.

---

## 🚀 Advanced Setup

### Using Conda Instead of venv

```bash
conda create -n whisper python=3.10
conda activate whisper
pip install -r requirements.txt
python src/gui.py
```

### Using Docker

```bash
# Build image
docker build -t whisperit .

# Run container
docker run -it -v $(pwd):/app whisperit
```

---

## ✅ Success Checklist

After setup, verify:
- [ ] Virtual environment created and activated
- [ ] `python --version` shows 3.8+
- [ ] `pip list` shows whisper and PySimpleGUI
- [ ] `python src/gui.py` opens a window
- [ ] Can select a file without errors
- [ ] Output directory is writable

If all check ✓, you're ready to transcribe!

---

**Questions?** Check `README.md` for more details.

**Happy transcribing!** 🎙️
