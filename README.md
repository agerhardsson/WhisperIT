# WhisperIT


Transcribe audio and video files using a modern GUI or interactive CLI, powered by faster-whisper.

## Quick Start

**Requirements:** Conda ([Miniconda or Anaconda](https://www.anaconda.com/docs/getting-started/miniconda/main))


```bash
cd <path>/WhisperIT
./run.sh setup      # One-time: create conda env and install dependencies
./run.sh gui        # Launch the GUI (default)
./run.sh cli        # Launch the interactive CLI
./run.sh update     # Update dependencies
```

The script will:
- Create a conda environment with Python 3.11 (if needed)
- Install all dependencies
- Launch the GUI or CLI as requested

## Features

- 🖥️ **Modern GUI** - PyQt6-based graphical interface
- 💻 **Interactive CLI** - Step-based terminal interface (no arguments needed)
- 📁 **Batch Processing** - Transcribe multiple files simultaneously
- 💤 **Background Transcription** - Continues during screen lock and minimized
- 📝 **Accurate Transcription** - Using faster-whisper for optimal performance
- 🌍 **99+ Languages** with auto-detection
- 📊 **Multiple Formats** - TXT, JSON, SRT, TSV, Summary JSON
- ⚙️ **5 Model Sizes** - tiny to large (choose speed vs accuracy)
- 🎬 **13+ File Formats** - MP3, MP4, WAV, MKV, and more
- 🚀 **One-Command Setup** - `./run.sh setup` handles everything

## Supported Formats

**Audio**: MP3, WAV, M4A, FLAC, OGG, AAC, Opus  
**Video**: MP4, MKV, MOV, AVI, FLV, WMV, WebM

## Models

| Model | Speed | Size | Best For |
|-------|-------|------|----------|
| tiny | ⚡⚡⚡ Fastest | 80MB | Quick transcriptions |
| base | ⚡⚡ Fast | 140MB | **Recommended** |
| small | ⚡ Balanced | 461MB | Better accuracy |
| medium | 🐢 Slow | 1.5GB | High accuracy |
| large | 🐢🐢 Slowest | 2.9GB | Highest accuracy |

## Output

Transcription generates up to 4 files:
- `filename.txt` - Plain text
- `filename.json` - Structured with timestamps
- `filename.tsv` - Tab-separated format
- `filename_summary.json` - Metadata

## Requirements

- **Conda** (Miniconda or Anaconda) - [Install here](https://docs.conda.io/projects/miniconda/en/latest/)
- ~5-10 GB disk space (for model downloads)
- 2+ GB RAM

## Installation

The `bash run.sh` script handles everything automatically:
- Checks for conda installation
- Creates a `whisperit` conda environment with Python 3.11
- Installs all dependencies from `requirements.txt`
- Launches the PyQt6 GUI application

**First time setup:**
```bash
bash run.sh
```

**Subsequent launches:**
```bash
bash run.sh  # Conda environment already exists, just activates and launches
```

## Usage Example


### GUI (default)
```bash
./run.sh gui
```
Follow the on-screen instructions in the PyQt6 window.

### Interactive CLI
```bash
./run.sh cli
```
You will be guided step-by-step to select model, language, input/output folders, formats, and overwrite options.

### Direct CLI (batch mode)
```bash
./run.sh cli -i <input_dir> -o <output_dir> [-m model] [-l lang] [-f formats] [--overwrite]
```
Example:
```bash
./run.sh cli -i ./audio -o ./transcripts -m base -l en -f txt srt --overwrite
```

## Tips

- **First run** will download the model (~100MB+), cached for future use
- **Transcription time**: ~1 hour audio ≈ 10-30 minutes on CPU with base model
- **Cancel anytime** with Ctrl+C
- **Run again** with `bash run.sh` - virtual environment is already set up

## Language Support

Supports all major languages including English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Japanese, Chinese, and 89+ more.

## Project Structure


```
src/
  transcriber.py    - Core transcription engine (faster-whisper)
  gui.py            - PyQt6 GUI
  cli.py            - Interactive and batch CLI
run.sh              - Setup and launch script
requirements.txt    - Python dependencies
```

## Keyboard Shortcuts

- **Ctrl+C** - Cancel transcription

---


---
For detailed documentation, see the `docs` branch.
