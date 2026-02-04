# WhisperIT - Audio/Video Transcription Application

A minimal, user-friendly desktop application for transcribing audio and video files using OpenAI Whisper.

## Features

✓ **Clean GUI** - Simple, intuitive interface built with PySimpleGUI  
✓ **Multiple Input Formats** - Supports MP3, WAV, M4A, FLAC, OGG, AAC, MP4, MKV, MOV, AVI, FLV, WMV, WebM  
✓ **Multiple Output Formats** - Save as TXT, JSON, or TSV (with timestamps)  
✓ **Language Support** - Auto-detect or select from 99+ languages  
✓ **Model Selection** - Choose from Whisper models: tiny, base, small, medium, large  
✓ **Non-blocking UI** - Transcription runs in background, UI stays responsive  
✓ **Smart Output** - Generates summary JSON with metadata and processing details  
✓ **Easy Installation** - Minimal dependencies, clear setup instructions  

## System Requirements

- **Python 3.8+** (Recommended: Python 3.10 or higher)
- **macOS, Linux, or Windows**
- **~5-10 GB free disk space** (for model downloads on first run)
- **2+ GB RAM** (more recommended for larger models)

## Installation

### Step 1: Create a Python Virtual Environment

```bash
# Navigate to the project directory
cd /Users/andreas.gerhardsson/Sites/WhisperIT

# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# or on Windows:
# venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

The installation may take a few minutes. On the first transcription, Whisper will download the selected model (~140MB for 'tiny' to ~3GB for 'large'). This is a one-time download.

### Step 3: Run the Application

```bash
# Make sure you're in the project directory and virtual environment is activated
python src/gui.py
```

A GUI window will appear. You're ready to transcribe!

## Usage

### Basic Workflow

1. **Select a File**
   - Click "Browse" to select an audio or video file
   - Supported formats: MP3, WAV, M4A, FLAC, OGG, AAC (audio) or MP4, MKV, MOV, AVI, FLV, WMV, WebM (video)

2. **Configure Settings**
   - **Model**: Choose transcription accuracy vs. speed
     - `tiny`: Fastest, least accurate (~80MB)
     - `base`: Good balance (~140MB)
     - `small`: More accurate (~461MB)
     - `medium`: High accuracy (~1.5GB)
     - `large`: Highest accuracy (~2.9GB)
   - **Language**: Select language or use "Auto-detect"
   - **Output Directory**: Where to save transcription files
   - **Output Formats**: Choose which file formats to generate

3. **Start Transcription**
   - Click "START" button
   - The status panel shows live progress
   - Wait for "✓ Finished!" message

4. **Access Your Output**
   - Files are saved in the Output Directory
   - You get up to 4 files per transcription:
     - `filename.txt` - Plain text transcript
     - `filename.json` - Full transcript with segment data
     - `filename.tsv` - Timestamps and text (for editing/subtitles)
     - `filename_summary.json` - Metadata and processing info

### Model Selection Guide

| Model | Speed | Accuracy | Size | Language Support |
|-------|-------|----------|------|------------------|
| tiny | ⚡⚡⚡ | ⭐ | 80MB | 99+ |
| base | ⚡⚡ | ⭐⭐ | 140MB | 99+ |
| small | ⚡ | ⭐⭐⭐ | 461MB | 99+ |
| medium | 🐢 | ⭐⭐⭐⭐ | 1.5GB | 99+ |
| large | 🐢🐢 | ⭐⭐⭐⭐⭐ | 2.9GB | 99+ |

For most use cases, **`base`** offers the best balance of speed and accuracy.

## Output Files Explained

### `.txt` - Plain Text
Simple transcription text, one paragraph per line.

```
This is the transcribed audio content.
All the speech is converted to text.
```

### `.json` - Full Transcript
Complete transcript with language info and segment-level data.

```json
{
  "text": "Full transcript...",
  "language": "en",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "First segment text...",
      "tokens": [...],
      "temperature": 0.0,
      "avg_logprob": -0.234,
      "compression_ratio": 1.234,
      "no_speech_prob": 0.001
    }
  ]
}
```

### `.tsv` - Segments with Timestamps
Tab-separated format ideal for editing, creating subtitles, or importing to other tools.

```
start	end	text
0.00	5.20	First segment text
5.20	10.45	Second segment text
```

### `_summary.json` - Metadata
Processing information and a preview of the transcript.

```json
{
  "timestamp": "2024-02-04T10:30:45.123456",
  "input_file": "meeting.mp4",
  "model": "base",
  "language": "auto",
  "detected_language": "en",
  "duration_seconds": 3600,
  "output_files": {
    "txt": "/path/to/meeting.txt",
    "json": "/path/to/meeting.json",
    "tsv": "/path/to/meeting.tsv"
  },
  "text_preview": "First 200 characters of transcript..."
}
```

## Troubleshooting

### Issue: "OpenAI Whisper not installed"
**Solution:** Ensure you activated the virtual environment and installed dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "ModuleNotFoundError: No module named 'PySimpleGUI'"
**Solution:** Install the requirements:
```bash
pip install -r requirements.txt
```

### Issue: "No such file or directory: ~/.cache/whisper" 
**Solution:** This is normal on first run. Whisper downloads models automatically. Ensure you have internet connection and ~3GB free disk space.

### Issue: Application is slow or unresponsive during transcription
**Solution:** This is normal for large audio files or slower models. The UI will be responsive again once transcription completes. You can click "STOP" to cancel the current transcription.

### Issue: File permission denied when saving
**Solution:** Check that the Output Directory is writable. You can select a different directory (e.g., Documents folder) in the settings.

### Issue: Unsupported file format error
**Solution:** The application only supports the formats listed in the "Supported Formats" section. Convert your file using FFmpeg:
```bash
# Convert video to MP4
ffmpeg -i input.mov -c:v libx264 -preset medium output.mp4

# Convert audio to MP3
ffmpeg -i input.flac -q:a 0 -map a output.mp3
```

## Project Structure

```
WhisperIT/
├── src/
│   ├── gui.py              # Main GUI application
│   └── transcriber.py      # Transcription logic and file I/O
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── run.sh                 # Quick start script (optional)
```

### File Descriptions

**`gui.py`** - PySimpleGUI application  
- Handles user interface and interactions
- Manages status updates from transcription worker
- Provides settings panel for model, language, and output selection

**`transcriber.py`** - Core transcription logic  
- `TranscriptionWorker` class handles background transcription
- Supports multiple output formats (TXT, JSON, TSV)
- Generates metadata summary for each transcription
- Thread-safe status callbacks for GUI updates

**`requirements.txt`** - Python package dependencies  
Minimal, pinned versions for reproducibility

## Advanced Usage

### Running from Terminal with Custom Settings

You can modify `src/gui.py` to set default values:

```python
# In gui.py, line ~80, change defaults:
sg.Combo(self.worker.AVAILABLE_MODELS, default_value='small',  # Changed from 'base'
```

### Deactivating Virtual Environment

When done, deactivate the virtual environment:
```bash
deactivate
```

To use WhisperIT again, just run `source venv/bin/activate` from the project directory.

## Alternative Implementations

### Using faster-whisper (2-5x faster)

For faster transcription with lower CPU usage, you can install `faster-whisper`:

1. **Update requirements.txt** - Uncomment the `faster-whisper` line
2. **Modify transcriber.py** - Change imports (instructions in comments)
3. This reduces transcription time significantly but uses less RAM

### Running in Background with tmux

For long transcriptions that you want to run in the background:

```bash
# In your terminal
tmux new-session -d -s whisper "cd ~/Sites/WhisperIT && source venv/bin/activate && python src/gui.py"

# List sessions
tmux list-sessions

# Attach to see the GUI
tmux attach-session -t whisper
```

## Supported Languages

99+ languages supported. Full list in `src/transcriber.py` in the `LANGUAGES` dictionary.

Common languages include: English, Spanish, French, German, Mandarin, Japanese, Korean, Russian, Arabic, Hindi, Portuguese, and many more.

## Performance Tips

1. **Model Selection** - Use `tiny` or `base` for quick transcriptions, `large` for maximum accuracy
2. **GPU Support** - If you have CUDA or Metal support, Whisper will use it automatically
3. **File Format** - MP3 and MP4 files transcribe faster than WAV or MKV
4. **Longer Files** - For files >1 hour, expect proportionally longer processing time

## License

This application uses OpenAI's Whisper, which is available under the MIT License.

## Support

For issues with OpenAI Whisper, visit: https://github.com/openai/whisper

For issues with this application, check the Troubleshooting section above.

---

**Happy Transcribing! 🎙️**
