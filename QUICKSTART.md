# WhisperIT - Quick Start Guide

## Overview

**WhisperIT** is a powerful command-line application for transcribing audio and video files using OpenAI's Whisper model. It supports 99+ languages, multiple output formats (TXT, JSON, TSV), and various model sizes from tiny (80MB) to large (2.9GB).

## What You Get

✅ **Full transcription** of audio/video files  
✅ **Multiple output formats** (plain text, JSON with segments, timestamped TSV)  
✅ **99+ language support** with auto-detection  
✅ **5 model sizes** from fastest to most accurate  
✅ **Zero setup** - automated installation and configuration  
✅ **Production-ready** error handling  

## Installation

### Step 1: Navigate to the project directory
```bash
cd /Users/andreas.gerhardsson/Sites/WhisperIT
```

### Step 2: Run the setup and start the app
```bash
bash run.sh
```

That's it! The script will:
- Create a Python 3.14 virtual environment
- Install all dependencies (Whisper, PyTorch, audio libraries)
- Launch the interactive transcription app

## Usage

When you run `bash run.sh`, you'll see an interactive menu:

### Step 1: Select Your Audio/Video File
```
Enter path to audio/video file: /path/to/your/audio.mp3
```
- Supports MP3, WAV, M4A, FLAC, OGG, AAC, MP4, MKV, MOV, AVI, FLV, WMV, WebM

### Step 2: Choose a Model
```
Available models:
  1. tiny     - 80MB - Fastest
  2. base     - 140MB - Balanced (Recommended)
  3. small    - 461MB - More accurate
  4. medium   - 1.5GB - High accuracy
  5. large    - 2.9GB - Highest accuracy

Select model (1-5, or name): base
```

### Step 3: Select Language
```
99 languages available:
  Option 1: Auto-detect (default)
  Option 2: Enter language code (e.g., 'en', 'es', 'fr')
  Option 3: Search for language name

Select option (1-3) or enter language code: 1
```

### Step 4: Choose Output Directory
```
Output directory [~/Transcriptions]: 
```
Press Enter to use default, or specify a custom directory.

### Step 5: Select Output Formats
```
Output formats:
  1. TXT - Plain text transcript
  2. JSON - Structured data with segments
  3. TSV - Tab-separated with timestamps

Select formats (e.g., '1,2,3' or 'all') [1,2,3]: 1,2,3
```

### Step 6: Confirm and Start
The app will show a summary of your settings. Confirm with `y` to start transcription.

## Example Workflow

```bash
# Run the app
$ bash run.sh

# Follow the prompts
Enter path to audio/video file: ~/Downloads/meeting.mp3
✓ Selected file

[Model selection...]
Selected model: base

[Language selection...]
Selected language: Auto-detect

[Output directory...]
Output directory: ~/Transcriptions

[Format selection...]
Selected formats: txt, json, tsv

===== Summary =====
Input file:      meeting.mp3
Model:           base
Language:        Auto-detect
Output dir:      ~/Transcriptions
Formats:         txt, json, tsv
==================

Start transcription? (y/n): y

Transcription in progress. This may take a while...
✓ Transcription complete!
✓ Output files saved to: ~/Transcriptions
```

## Output Files

After transcription, you'll get up to 4 files in your output directory:

- **`meeting.txt`** - Plain text transcript
- **`meeting.json`** - Structured transcript with word-level timestamps
- **`meeting.tsv`** - Tab-separated format with timestamps
- **`meeting_summary.json`** - Metadata about the transcription

## Supported Formats

### Audio Formats
MP3, WAV, M4A, FLAC, OGG, AAC, Opus

### Video Formats
MP4, MKV, MOV, AVI, FLV, WMV, WebM, etc.

## Language Support

All major languages are supported, including:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)
- Russian (ru)
- Japanese (ja)
- Chinese (zh)
- And 89+ more...

## Tips & Tricks

### Model Selection Guide
- **Tiny (80MB)**: Best for fast transcription on weak hardware, reasonable accuracy
- **Base (140MB)**: Good balance of speed and accuracy - **recommended for most users**
- **Small (461MB)**: Better accuracy, slower
- **Medium (1.5GB)**: High accuracy, slower
- **Large (2.9GB)**: Highest accuracy, slowest - requires 4GB+ RAM

### Keyboard Shortcuts
- **Ctrl+C**: Cancel transcription at any time

### Language Search
In the language selection menu, choose option 3 to search for a language:
```
Search for language: portuguese
Found 1 matches:
  1. Portuguese (pt)
```

### Running Again
Just run `bash run.sh` again - your virtual environment is already set up, so subsequent runs are faster.

## Troubleshooting

### "File not found" error
Make sure you provide the full path or a path relative to where you're running the command.

### Transcription is slow
The first run with a model downloads it (100MB+). Subsequent runs are faster. Use a smaller model for faster transcription.

### Virtual environment issues
To manually activate the virtual environment:
```bash
source venv/bin/activate
python src/gui.py
```

### Out of memory error
Use a smaller model (tiny, base, or small instead of medium/large).

## Architecture

WhisperIT is built with a clean, modular architecture:

- **`src/transcriber.py`** (302 lines)
  - Core transcription engine
  - Threading for non-blocking operation
  - Output file generation
  - Language detection support

- **`src/gui.py`** (266 lines)
  - Interactive command-line interface
  - Input validation
  - Settings configuration

- **`run.sh`** (55 lines)
  - Automated setup and startup
  - Dependency management
  - Virtual environment handling

## Performance Notes

Transcription time depends on:
1. Audio length
2. Model size (tiny is 3-5x faster than large)
3. Hardware (GPU support dramatically speeds things up)
4. Language complexity

A typical 1-hour audio file with the base model on CPU takes 10-30 minutes.

## Support

All dependencies are automatically installed. The app is self-contained and doesn't require external configuration.

For full documentation, see:
- `README.md` - Project overview
- `ARCHITECTURE.md` - Technical details
- `INDEX.md` - Documentation index

---

**Ready to transcribe?** Run `bash run.sh` and follow the prompts! 🎙️
