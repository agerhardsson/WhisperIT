"""
WhisperIT - Audio/Video Transcription CLI Application
A clean, simple command-line interface for transcribing audio and video files using OpenAI Whisper.
"""

import sys
from pathlib import Path
from transcriber import TranscriptionWorker, WHISPER_AVAILABLE
import time


def print_header():
    """Print application header."""
    print("\n" + "="*70)
    print("  🎙️  WHISPERIT - Audio/Video Transcription  🎙️  ")
    print("="*70 + "\n")


def select_file():
    """Prompt user to select an audio/video file."""
    while True:
        try:
            file_path = input("Enter path to audio/video file: ").strip()
        except EOFError:
            print("\n❌ ERROR: No input provided. Exiting.\n")
            sys.exit(1)
        
        if not file_path:
            print("❌ Please provide a file path.\n")
            continue
        
        # Handle quoted paths
        file_path = file_path.strip('"\'')
        
        path_obj = Path(file_path).expanduser()
        
        if not path_obj.exists():
            print(f"❌ File not found: {file_path}\n")
            continue
        
        return str(path_obj)


def select_model():
    """Prompt user to select a model."""
    models = ['tiny', 'base', 'small', 'medium', 'large']
    
    while True:
        print("\nAvailable models:")
        for i, model in enumerate(models, 1):
            size_info = {
                'tiny': '80MB - Fastest',
                'base': '140MB - Balanced (Recommended)',
                'small': '461MB - More accurate',
                'medium': '1.5GB - High accuracy',
                'large': '2.9GB - Highest accuracy'
            }
            print(f"  {i}. {model} - {size_info.get(model, '')}")
        
        choice = input("\nSelect model (1-5, or name): ").strip().lower()
        
        # Handle numeric choice
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]
            else:
                print("❌ Invalid selection. Please choose 1-5.\n")
                continue
        
        # Handle name choice
        if choice in models:
            return choice
        
        print("❌ Invalid model. Please choose from: tiny, base, small, medium, large\n")


def select_language(worker):
    """Prompt user to select a language."""
    languages = list(worker.LANGUAGES.items())
    
    print(f"\n{len(languages)} languages available:")
    print("  Option 1: Auto-detect (default) - Automatically detect language")
    print("  Option 2: Enter language code (e.g., 'en', 'es', 'fr')")
    print("  Option 3: Search for language name")
    
    try:
        choice = input("\nSelect option (1-3) or enter language code: ").strip().lower()
    except EOFError:
        print("\n❌ ERROR: No input provided. Exiting.\n")
        sys.exit(1)
    
    if choice == '1' or choice == 'auto':
        return 'auto'
    
    elif choice == '3':
        try:
            search_term = input("Search for language: ").strip().lower()
        except EOFError:
            print("\n❌ ERROR: No input provided. Using auto-detect.\n")
            return 'auto'
        
        matches = [(k, v) for k, v in languages if search_term in v.lower()]
        
        if not matches:
            print(f"❌ No languages found matching '{search_term}'. Using auto-detect.\n")
            return 'auto'
        
        if len(matches) == 1:
            return matches[0][0]
        
        print(f"\nFound {len(matches)} matches:")
        for i, (code, name) in enumerate(matches[:10], 1):
            print(f"  {i}. {name} ({code})")
        
        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more")
        
        try:
            sub_choice = input(f"\nSelect (1-{min(10, len(matches))}): ").strip()
        except EOFError:
            print("\nUsing auto-detect.\n")
            return 'auto'
        
        if sub_choice.isdigit():
            idx = int(sub_choice) - 1
            if 0 <= idx < min(10, len(matches)):
                return matches[idx][0]
        
        print("Using auto-detect.\n")
        return 'auto'
    
    # Try to use the input as a language code
    if choice in worker.LANGUAGES:
        return choice
    
    # Try to find a matching language by name
    for code, name in languages:
        if name.lower() == choice:
            return code
    
    print(f"❌ Language '{choice}' not found. Using auto-detect.\n")
    return 'auto'


def select_output_dir():
    """Prompt user to select output directory."""
    default = str(Path.home() / 'Transcriptions')
    
    try:
        user_input = input(f"\nOutput directory [{default}]: ").strip()
    except EOFError:
        print(f"Using default directory: {default}\n")
        return default
    
    if not user_input:
        return default
    
    output_path = Path(user_input).expanduser()
    return str(output_path)


def select_output_formats():
    """Prompt user to select output formats."""
    print("\nOutput formats:")
    print("  1. TXT - Plain text transcript")
    print("  2. JSON - Structured data with segments")
    print("  3. TSV - Tab-separated with timestamps")
    
    try:
        choice = input("\nSelect formats (e.g., '1,2,3' or 'all') [1,2,3]: ").strip().lower()
    except EOFError:
        print("Using default formats: TXT, JSON, TSV\n")
        return ['txt', 'json', 'tsv']
    
    if not choice or choice == 'all':
        return ['txt', 'json', 'tsv']
    
    format_map = {'1': 'txt', '2': 'json', '3': 'tsv'}
    formats = []
    
    for item in choice.split(','):
        item = item.strip()
        if item in format_map:
            formats.append(format_map[item])
    
    if not formats:
        print("No valid formats selected. Using all formats.\n")
        return ['txt', 'json', 'tsv']
    
    return formats


def main():
    """Main application."""
    print_header()
    
    # Initialize worker
    worker = TranscriptionWorker(status_callback=print)
    
    if not WHISPER_AVAILABLE:
        print("❌ ERROR: OpenAI Whisper not installed!")
        print("   Run: pip install -r requirements.txt\n")
        sys.exit(1)
    
    try:
        # Get input from user
        print("Step 1: Select audio/video file")
        file_path = select_file()
        
        if not worker.is_supported_file(file_path):
            print("\n❌ ERROR: File format not supported!")
            print("   Supported: MP3, WAV, M4A, FLAC, OGG, AAC (audio) | MP4, MKV, MOV, AVI, FLV, WMV, WebM (video)\n")
            sys.exit(1)
        
        print(f"\n✓ Selected: {Path(file_path).name}\n")
        
        # Get transcription settings
        print("Step 2: Select transcription model")
        model = select_model()
        print(f"\n✓ Selected model: {model}\n")
        
        print("Step 3: Select language")
        language = select_language(worker)
        lang_display = "Auto-detect" if language == 'auto' else worker.LANGUAGES.get(language, language)
        print(f"✓ Selected language: {lang_display}\n")
        
        print("Step 4: Select output directory")
        output_dir = select_output_dir()
        print(f"✓ Output directory: {output_dir}\n")
        
        print("Step 5: Select output formats")
        output_formats = select_output_formats()
        print(f"✓ Selected formats: {', '.join(output_formats)}\n")
        
        # Confirm settings
        print("="*70)
        print("Summary:")
        print(f"  Input file:      {Path(file_path).name}")
        print(f"  Model:           {model}")
        print(f"  Language:        {lang_display}")
        print(f"  Output dir:      {output_dir}")
        print(f"  Formats:         {', '.join(output_formats)}")
        print("="*70 + "\n")
        
        try:
            confirm = input("Start transcription? (y/n): ").strip().lower()
        except EOFError:
            print("\n❌ ERROR: No input provided. Exiting.\n")
            sys.exit(1)
        
        if confirm != 'y':
            print("Cancelled.\n")
            sys.exit(0)
        
        # Start transcription
        print("\n" + "-"*70)
        print("Starting transcription...")
        print("-"*70 + "\n")
        
        success = worker.transcribe(file_path, output_dir, model, language, output_formats)
        
        if success:
            # Wait for completion
            print("\nTranscription in progress. This may take a while...")
            while worker.is_transcribing():
                time.sleep(1)
            
            print("\n" + "="*70)
            print("✓ Transcription complete!")
            print(f"✓ Output files saved to: {output_dir}")
            print("="*70 + "\n")
        else:
            print("\n❌ Failed to start transcription.\n")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Transcription cancelled by user.")
        worker.stop()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
