# WhisperIT

Transcribe audio and video files using a PyQt6 desktop GUI or interactive CLI, powered by faster-whisper.

## Install And Run

### Packaged builds

Download the archive for your operating system from the repository's GitHub Actions `Package WhisperIT` workflow artifacts, or from a release when available. Extract it and launch the GUI bundle. The archive also includes a CLI bundle. These initial builds are unsigned; macOS may require approving the app in Privacy & Security before opening it.

The app downloads the selected Whisper model the first time it is used. Models are cached for later runs and are not included in the application archive. CI builds Apple Silicon and Intel macOS bundles, a Linux bundle on Ubuntu 22.04, and a Windows bundle. Linux compatibility outside Ubuntu 22.04-based distributions has not yet been validated.

### Run from source

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first. uv manages the Python 3.11/3.12 environment and dependencies.

macOS/Linux:

```bash
./run.sh setup
./run.sh gui
./run.sh cli
./run.sh update
```

Windows PowerShell:

```powershell
.\run.ps1 setup
.\run.ps1 gui
.\run.ps1 cli
.\run.ps1 update
```

To run the batch CLI, pass its options after `cli`:

```bash
./run.sh cli -i ./audio -o ./transcripts -m base -l en -f txt srt --overwrite
```

```powershell
.\run.ps1 cli -i .\audio -o .\transcripts -m base -l en -f txt srt --overwrite
```

`update` explicitly upgrades dependencies and refreshes `uv.lock`. For normal development, `uv sync --locked` installs the exact committed versions.

## Development

```bash
uv sync --group dev
uv run whisperit-gui
uv run whisperit --help
```

The committed `uv.lock` is the dependency source of truth. Python 3.11 and 3.12 are supported.

## Packaging

The `.github/workflows/package.yml` workflow builds separate PyInstaller GUI and CLI bundles on macOS, Linux, and Windows. It runs on `workflow_dispatch` or when a `v*` tag is pushed. Bundles are uploaded as workflow artifacts. Builds are currently unsigned and are not DMG/MSI/AppImage installers; signing, notarization, and OS-specific installer formats can be added for releases.

## Features

- PyQt6 GUI with drag-and-drop, batch queues, progress, and system tray support
- Interactive and batch CLI
- faster-whisper transcription with automatic language detection
- TXT, JSON, SRT, TSV, and summary JSON output
- tiny, base, small, medium, and large model sizes
- Audio formats: MP3, WAV, M4A, FLAC, OGG, AAC
- Video formats: MP4, MKV, MOV, AVI, FLV, WMV, WebM

## Models

| Model | Approximate size | Typical use |
|---|---:|---|
| tiny | 80 MB | Fast drafts |
| base | 140 MB | Recommended starting point |
| small | 461 MB | Higher accuracy |
| medium | 1.5 GB | High accuracy |
| large | 2.9 GB | Highest accuracy |

Model sizes and performance vary by compute type and platform. Allow additional disk space for downloaded models and temporary files.

## Output

For each input file, WhisperIT can write selected `.txt`, `.json`, `.srt`, and `.tsv` files plus a metadata summary JSON.
