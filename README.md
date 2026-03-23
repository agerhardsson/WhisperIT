# WhisperIT

A simple GUI for transcribing audio and video files using OpenAI Whisper.

## Quick Start

**Requirements:** Conda ([Miniconda or Anaconda](https://www.anaconda.com/docs/getting-started/miniconda/main))

```bash
cd /Users/andreas.gerhardsson/Sites/WhisperIT
bash run.sh
```

The script will:
1. Create a conda environment with Python 3.11
2. Install all dependencies
3. Launch the GUI application

## Features

- 🖥️ **Modern GUI** - PyQt6-based graphical interface
- 📁 **Batch Processing** - Transcribe multiple files simultaneously
- 💤 **Background Transcription** - Continues during screen lock and minimized
- 📝 **Accurate Transcription** - Using faster-whisper for optimal performance
- 🌍 **99+ Languages** with auto-detection
- 📊 **Multiple Formats** - TXT, JSON, TSV, Summary JSON
- ⚙️ **5 Model Sizes** - tiny to large (choose speed vs accuracy)
- 🎬 **13+ File Formats** - MP3, MP4, WAV, MKV, and more
- 🚀 **One-Command Setup** - `bash run.sh` handles everything

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

```bash
$ bash run.sh

WhisperIT - Audio/Video Transcription Application

Conda environment 'whisperit' activated
Installing dependencies...
✓ Ready! Starting WhisperIT...

[PyQt6 GUI window opens]
```

Then in the GUI:
1. Click "Add Files..." to select audio/video files
2. Configure model, language, and output directory
3. Choose output formats (TXT, JSON, TSV)
4. Click "Start Transcription"
5. App can be minimized/closed - transcription continues in background

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
  transcriber.py    - Core transcription engine
  gui.py            - Interactive CLI interface
run.sh              - Setup and launch script
requirements.txt    - Python dependencies
```

## Keyboard Shortcuts

- **Ctrl+C** - Cancel transcription

---

For detailed documentation, see the `docs` branch.
