# WhisperIT - Architecture & Code Overview

## Project Architecture

```
User (GUI Application)
        ↓
   gui.py (PySimpleGUI)
        ↓
TranscriptionGUI class
        ↓
   TranscriptionWorker (in transcriber.py)
        ↓
Background Thread (non-blocking)
        ↓
Whisper Model (OpenAI)
        ↓
Output Files (.txt, .json, .tsv, _summary.json)
```

---

## Core Components

### 1. **gui.py** - The User Interface

**Purpose:** Create and manage the graphical user interface using PySimpleGUI

**Key Classes:**
- `TranscriptionGUI` - Main application window and event loop

**Key Methods:**
- `build_layout()` - Creates the GUI layout with all elements
- `update_status()` - Receives status messages from worker thread
- `run()` - Main event loop that handles user interactions

**GUI Elements:**
| Element | Purpose |
|---------|---------|
| File Browser | Select audio/video file to transcribe |
| Model Dropdown | Choose transcription model (tiny→large) |
| Language Dropdown | Select language (99+ supported) |
| Output Directory | Choose where to save results |
| Format Checkboxes | Select output formats (TXT/JSON/TSV) |
| START Button | Begin transcription |
| STOP Button | Cancel in-progress transcription |
| Status Panel | Display real-time progress |

**How It Works:**
1. User selects file and settings
2. Clicks START button
3. GUI calls `worker.transcribe()` in background thread
4. UI remains responsive while transcription happens
5. Status messages update in real-time
6. When done, START button re-enables

---

### 2. **transcriber.py** - The Engine

**Purpose:** Handle transcription logic, file I/O, and background threading

**Key Classes:**
- `TranscriptionWorker` - Manages transcription in background thread

**Key Attributes:**
```python
SUPPORTED_FORMATS      # List of audio/video extensions
AVAILABLE_MODELS       # Whisper model sizes
LANGUAGES              # 99+ language codes and names
status_callback        # Function to update GUI
is_running            # Boolean for thread state
current_thread        # Background thread reference
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `transcribe()` | Start transcription (returns immediately) |
| `_transcribe_worker()` | Background worker - does actual transcription |
| `is_supported_file()` | Check if file format is supported |
| `_save_txt()` | Save plain text transcript |
| `_save_json()` | Save structured JSON with segments |
| `_save_tsv()` | Save TSV with timestamps |
| `_save_summary()` | Save metadata JSON |
| `stop()` | Stop in-progress transcription |

**Threading Model:**
```
Main Thread (GUI)
    ↓
    └─→ .transcribe() called
        ↓
        └─→ Creates new thread
            ↓
            └─→ _transcribe_worker() runs
                ├─ Load model
                ├─ Process audio
                ├─ Save files
                └─ Updates GUI via callback
        ↓
    Event loop continues (non-blocking)
```

---

## Code Flow - From Start to Finish

### Scenario: User transcribes an audio file

```
1. User clicks "Browse" in GUI
   └─→ gui.py event handler opens file picker
   └─→ User selects audio file
   └─→ File path stored in GUI

2. User selects settings
   └─→ Model: "base"
   └─→ Language: "English"
   └─→ Output: ~/Transcriptions
   └─→ Formats: TXT, JSON, TSV

3. User clicks "START" button
   └─→ gui.py validates selection
   └─→ Calls worker.transcribe(file_path, output_dir, model, language, formats)
   └─→ Returns immediately (START disabled, STOP enabled)

4. Background thread starts in transcriber.py
   └─→ _transcribe_worker() begins
   └─→ Sends: "Starting transcription of audio.mp3..."
   └─→ Loads Whisper model: "Loading model 'base'..."
   └─→ Runs transcription (may take minutes)
   └─→ Sends: "Model loaded. Processing audio..."

5. Audio processing completes
   └─→ result = {text: "...", segments: [...]}

6. Generate output files
   └─→ Save .txt file → Sends: "✓ Saved: audio.txt"
   └─→ Save .json file → Sends: "✓ Saved: audio.json"
   └─→ Save .tsv file → Sends: "✓ Saved: audio.tsv"
   └─→ Save _summary.json → Sends: "✓ Saved: audio_summary.json"

7. Completion
   └─→ Sends: "✓ Finished!"
   └─→ is_running = False
   └─→ GUI enables START button, disables STOP button

8. User sees all 4 files in ~/Transcriptions directory
```

---

## Key Design Decisions

### 1. **Threading for Non-blocking UI**
- Transcription runs in separate thread
- GUI remains responsive during processing
- User can still interact with UI or stop transcription

### 2. **Status Callback Pattern**
- Worker thread calls `status_callback()` to send messages
- Avoids thread safety issues with GUI updates
- Main thread reads messages during event loop

### 3. **Multiple Output Formats**
- **TXT:** Simple, readable, shareable
- **JSON:** Machine-readable, includes segment-level data
- **TSV:** Import into spreadsheets, editing tools, subtitle editors

### 4. **Metadata Summary**
- Tracks what model/language was used
- Records processing timestamp
- Stores file paths and preview
- Useful for batch processing or auditing

### 5. **Language Support**
- Maps display names (friendly) to codes (for Whisper API)
- 99+ languages from Whisper's training data
- Auto-detection as default option

### 6. **Model Flexibility**
- User chooses speed vs accuracy tradeoff
- Tiny (~80MB, fast) through Large (~3GB, accurate)
- Models auto-download on first use

---

## Data Structures

### Whisper Result Format
```python
result = {
    'text': 'Full transcript text...',
    'segments': [
        {
            'id': 0,
            'seek': 0,
            'start': 0.0,        # Start timestamp (seconds)
            'end': 5.2,          # End timestamp (seconds)
            'text': 'Segment text',
            'tokens': [1, 2, 3],
            'temperature': 0.0,
            'avg_logprob': -0.234,
            'compression_ratio': 1.2,
            'no_speech_prob': 0.001
        },
        # ... more segments
    ],
    'language': 'en'
}
```

### Output Summary JSON
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
  "text_preview": "First 200 characters..."
}
```

---

## Configuration & Constants

### TranscriptionWorker Class Constants

```python
# Supported file formats (by type)
SUPPORTED_FORMATS = {
    'audio': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
    'video': ['.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.webm']
}

# Available Whisper models
AVAILABLE_MODELS = ['tiny', 'base', 'small', 'medium', 'large']

# Language codes and display names (99 languages)
LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    # ... 97 more languages
}
```

---

## Error Handling

The application handles common errors gracefully:

| Error | Handling |
|-------|----------|
| File not found | Display error message in status |
| Unsupported format | Reject file, show supported formats |
| No internet (on first run) | Whisper shows error, user can retry |
| Permission denied (output) | Show error, suggest different directory |
| Model download interrupted | User can restart transcription |
| Out of memory (large model) | Suggest smaller model |

---

## Performance Considerations

### Transcription Speed
- Depends on: audio length, model size, CPU speed
- Typical speeds:
  - `tiny`: ~real-time (1 hour audio = ~1 hour processing)
  - `base`: ~1-2x real-time
  - `large`: ~5-10x real-time

### Memory Usage
- Model in RAM: 500MB (tiny) to 10GB (large)
- Processing: 1-2GB additional
- Recommendation: 4GB+ RAM for `base` or larger models

### Storage
- Models cache: ~/.cache/whisper/ (~140MB to 3GB)
- Output files: ~1KB per minute of audio (text) to 50KB/min (JSON)

---

## Extension Points

### Adding New Output Formats

In `transcriber.py`:
```python
def _transcribe_worker(self, ...):
    # ... existing code ...
    
    if 'srt' in output_formats:  # Add SRT subtitle format
        srt_file = os.path.join(output_dir, f"{input_filename}.srt")
        self._save_srt(result, srt_file)
        output_paths['srt'] = srt_file

@staticmethod
def _save_srt(result: Dict[str, Any], output_file: str):
    """Save as SRT subtitle format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(result.get('segments', []), 1):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            f.write(f"{i}\n")
            f.write(f"{int(start//3600):02d}:{int(start%3600//60):02d}:{int(start%60):02d},000 --> {int(end//3600):02d}:{int(end%3600//60):02d}:{int(end%60):02d},000\n")
            f.write(f"{text}\n\n")
```

### Adding Language Filter
```python
# In gui.py, make language dropdown searchable
sg.Combo(
    list(self.worker.LANGUAGES.values()),
    default_value='Auto-detect',
    readonly=False,  # Allow typing to filter
    key='-LANGUAGE-',
    size=(15, 1)
)
```

### Using faster-whisper Instead

Replace in `transcriber.py`:
```python
# Instead of: import whisper
# Use: from faster_whisper import WhisperModel

# In _transcribe_worker:
# Instead of: whisper_model = whisper.load_model(model)
# Use: whisper_model = WhisperModel(model, device="auto")
```

---

## Testing Checklist

Before deployment, verify:

- [ ] All imports resolve correctly
- [ ] GUI opens and is responsive
- [ ] File browser works
- [ ] Settings dropdowns populate
- [ ] START button triggers transcription
- [ ] Status updates appear in real-time
- [ ] STOP button cancels transcription
- [ ] Output files are created correctly
- [ ] Summary JSON has correct metadata
- [ ] Different models work (test tiny, medium)
- [ ] Different languages work (test English, Spanish)
- [ ] Different formats produce correct output
- [ ] Error messages are clear and helpful

---

## Maintenance & Updates

### Regular Maintenance
```bash
# Check for updates to packages
pip list --outdated

# Update all packages (optional)
pip install --upgrade -r requirements.txt
```

### Updating Whisper Only
```bash
pip install --upgrade openai-whisper
```

### Clearing Model Cache (if needed)
```bash
rm -rf ~/.cache/whisper/
# Models will re-download on next use
```

---

## File Size Reference

| Component | Size |
|-----------|------|
| gui.py | ~10 KB |
| transcriber.py | ~15 KB |
| Total code | ~25 KB |
| Whisper model (tiny) | ~80 MB |
| Whisper model (base) | ~140 MB |
| Whisper model (medium) | ~1.5 GB |
| Whisper model (large) | ~2.9 GB |

---

This architecture prioritizes:
1. **Simplicity** - Easy to understand and modify
2. **Usability** - Clear UI, responsive interaction
3. **Reliability** - Thread-safe, good error handling
4. **Flexibility** - Multiple formats, language support, model options

Happy coding! 🚀
