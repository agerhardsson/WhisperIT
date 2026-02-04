# WhisperIT

A simple command-line tool for transcribing audio and video files using OpenAI Whisper.

## Quick Start

```bash
cd /Users/andreas.gerhardsson/Sites/WhisperIT
bash run.sh
```

Then follow the interactive prompts to:
1. Select your audio/video file
2. Choose a model (recommended: `base`)
3. Select language (recommended: auto-detect)
4. Choose output directory
5. Select output formats

## Features

- 📝 **Transcribe audio/video** to text
- 🌍 **99+ languages** with auto-detection
- 📊 **Multiple formats**: TXT, JSON, TSV, Summary JSON
- ⚙️ **5 model sizes** (tiny to large)
- 🎬 **13+ file formats** supported
- 🚀 **One-command setup** with `bash run.sh`

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

- Python 3.14+
- ~5-10 GB disk space (for model downloads)
- 2+ GB RAM

## Installation

The `bash run.sh` script handles everything:
- Creates virtual environment
- Installs dependencies
- Launches the application

No manual setup needed.

## Usage Example

```bash
$ bash run.sh

WhisperIT - Audio/Video Transcription Application

Step 1: Select audio/video file
Enter path to audio/video file: ~/Downloads/meeting.mp3
✓ Selected file

[Follow prompts for model, language, output directory, formats]

Start transcription? (y/n): y

Transcription in progress...
✓ Transcription complete!
✓ Output files saved to: ~/Transcriptions
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
  transcriber.py    - Core transcription engine
  gui.py            - Interactive CLI interface
run.sh              - Setup and launch script
requirements.txt    - Python dependencies
```

## Keyboard Shortcuts

- **Ctrl+C** - Cancel transcription

---

For detailed documentation, see the `docs` branch.
