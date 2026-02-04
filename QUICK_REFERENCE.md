# WhisperIT - Quick Reference Card

## 🎯 Start Here (60 seconds)

```bash
cd /Users/andreas.gerhardsson/Sites/WhisperIT
chmod +x run.sh
./run.sh
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/gui.py
```

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Full user guide with features, usage, output formats |
| **SETUP.md** | Installation & troubleshooting (most helpful if issues arise) |
| **ARCHITECTURE.md** | Technical design, code flow, extension points |
| **QUICK_REFERENCE.md** | This file - quick lookup |

---

## 🎮 Using the GUI

1. **Click "Browse"** → Select audio/video file
2. **Choose Settings:**
   - Model: `tiny` (fast) → `large` (accurate)
   - Language: `Auto-detect` or specific language
   - Output: Directory to save files
   - Formats: Check at least one (TXT/JSON/TSV)
3. **Click "START"** → Wait for "✓ Finished!"
4. **Check Output Directory** → 4 files created

---

## 📁 What Gets Created

| File | Contains | Use Case |
|------|----------|----------|
| `.txt` | Plain text | Share with others, edit, copy-paste |
| `.json` | Segments + metadata | Import to apps, analyze, search |
| `.tsv` | Timestamps + text | Subtitles, spreadsheets, editing |
| `_summary.json` | Processing info | Track what settings were used |

---

## ⚡ Model Comparison (Quick)

| Model | Speed | Accuracy | Size | When to Use |
|-------|-------|----------|------|------------|
| tiny | ⚡⚡⚡ | ⭐ | 80MB | Quick drafts, low quality ok |
| base | ⚡⚡ | ⭐⭐ | 140MB | Default choice ✓ |
| small | ⚡ | ⭐⭐⭐ | 461MB | Important recordings |
| medium | 🐢 | ⭐⭐⭐⭐ | 1.5GB | High accuracy needed |
| large | 🐢🐢 | ⭐⭐⭐⭐⭐ | 2.9GB | Critical transcriptions |

**Recommendation:** Use `base` unless you have specific needs.

---

## 🌐 Common Languages

```
English (en)          | Spanish (es)         | French (fr)
German (de)          | Chinese (zh)         | Japanese (ja)
Korean (ko)          | Russian (ru)         | Arabic (ar)
Hindi (hi)           | Portuguese (pt)      | Italian (it)
```

Full list of 99+ languages in transcriber.py

---

## ❌ Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| `No module named whisper` | `pip install -r requirements.txt` |
| GUI won't open | Activate venv: `source venv/bin/activate` |
| Slow transcription | Use smaller model (`tiny`, `base`) |
| Permission denied (output) | Choose different directory (e.g., Documents) |
| Very large file fails | Use `large` model with patience, or split file |
| Can't find `ffmpeg` | `brew install ffmpeg` (macOS) |

---

## 🔧 Virtual Environment

**Activate:**
```bash
source venv/bin/activate
```

**Deactivate (when done):**
```bash
deactivate
```

**Check status:**
```bash
which python  # If shows venv/bin/python, you're activated
```

---

## 📊 File Sizes (Rough)

| Duration | .txt | .json | .tsv |
|----------|------|-------|------|
| 1 min | 1-2 KB | 5-10 KB | 2-3 KB |
| 1 hour | 100 KB | 500 KB | 200 KB |
| 10 hours | 1 MB | 5 MB | 2 MB |

Models download on first use (~140MB for base, cached for reuse).

---

## 🆘 Getting Help

1. **Application help:** Check README.md
2. **Setup help:** Check SETUP.md
3. **Code help:** Check ARCHITECTURE.md
4. **OpenAI Whisper help:** https://github.com/openai/whisper

---

## 🚀 Pro Tips

- **Batch process:** Can transcribe files one-by-one from command line
- **Better accuracy:** Use `medium` or `large` model
- **Faster transcription:** Use `tiny` model
- **Long files:** Start with `base`, use `large` only if needed
- **Multiple languages in file:** Use "Auto-detect"
- **Save space:** Only select needed output formats

---

## 💾 File Locations

**Output default:** `~/Transcriptions/` (changeable in app)

**Whisper models:** `~/.cache/whisper/` (auto-downloads)

**Config (optional):** `.whisperit_config.example` → copy to `.whisperit_config` to customize

---

## 📝 Python Version Requirements

```bash
python --version  # Should be 3.8 or higher
```

| Version | Status |
|---------|--------|
| 3.8 | Supported |
| 3.9 | Supported |
| 3.10 | Recommended ✓ |
| 3.11 | Supported |
| 3.12 | Supported |

---

## 🔄 Workflow Suggestions

### For Meetings/Lectures
1. Use `base` or `small` model
2. Language: Auto-detect or your language
3. Format: JSON (for searching) + TSV (for editing)

### For Podcasts
1. Use `base` model
2. Language: Auto-detect
3. Format: TXT (easy sharing)

### For Customer Service Recordings
1. Use `medium` or `large` model
2. Language: Specific (if known)
3. Format: All three (JSON for analysis, TXT for review, TSV for notes)

### For Batch Processing
1. Select `base` or `tiny` model
2. Set output to a batch folder
3. Process multiple files sequentially

---

## 📞 Emergency Cleanup

If something goes wrong and you want a fresh start:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Recreate
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/gui.py
```

---

## ✅ Checklist: Before Your First Transcription

- [ ] Python 3.8+ installed: `python --version`
- [ ] Virtual environment created: `ls -la | grep venv`
- [ ] Virtual environment activated: `(venv)` in prompt
- [ ] Dependencies installed: `pip list | grep whisper`
- [ ] GUI opens: `python src/gui.py`
- [ ] File browser works
- [ ] Have test audio file (~1-5 minutes recommended for first try)

---

**You're all set! Ready to transcribe.** 🎙️

See README.md for detailed user guide.
See SETUP.md if you hit any installation issues.
See ARCHITECTURE.md to understand how it works.
