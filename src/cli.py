#!/usr/bin/env python3
"""
WhisperIT CLI - Batch audio/video transcription using faster-whisper
"""
import argparse
import os
import sys
from pathlib import Path
from glob import glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcriber import TranscriptionWorker


def select_from_list(prompt, options, default_index=0):
    print(f"\n{prompt}")
    for i, option in enumerate(options):
        marker = "→" if i == default_index else " "
        print(f"  {marker} {i+1}. {option}")
    while True:
        try:
            choice = input(f"Select (1-{len(options)}) [default: {default_index+1}]: ").strip()
            if choice == "":
                return options[default_index]
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(options):
                return options[choice_num]
            print(f"❌ Invalid choice. Please enter 1-{len(options)}")
        except ValueError:
            print(f"❌ Please enter a number between 1-{len(options)}")

def confirm_path(prompt, default_path):
    print(f"\n{prompt}")
    print(f"Current: {default_path}")
    user_input = input("Press Enter to keep, or enter new path: ").strip()
    return user_input if user_input else default_path

def interactive_mode():
    print("\n╔════════════════════════════════════════╗")
    print("║     🎧 WhisperIT CLI Setup           ║")
    print("╚════════════════════════════════════════╝")
    models = TranscriptionWorker.AVAILABLE_MODELS
    default_model_idx = models.index('base')
    selected_model = select_from_list("📦 Select model:", models, default_model_idx)
    languages = list(TranscriptionWorker.LANGUAGES.keys())
    default_lang_idx = languages.index('auto')
    selected_language = select_from_list("🌍 Select language:", languages, default_lang_idx)
    input_dir = confirm_path("📂 Input directory:", str(Path.cwd()))
    output_dir = confirm_path("💾 Output directory:", str(Path.cwd()))
    all_formats = ['txt', 'json', 'srt', 'tsv']
    selected_formats = []
    print("\nSelect output formats (comma separated, e.g. 1,3 for txt,srt):")
    for i, fmt in enumerate(all_formats):
        print(f"  {i+1}. {fmt}")
    fmt_input = input("Formats [default: 1,2,3]: ").strip()
    if not fmt_input:
        selected_formats = ['txt', 'json', 'srt']
    else:
        try:
            idxs = [int(x.strip())-1 for x in fmt_input.split(',')]
            selected_formats = [all_formats[i] for i in idxs if 0 <= i < len(all_formats)]
        except Exception:
            selected_formats = ['txt', 'json', 'srt']
    overwrite = input("Overwrite existing outputs? (y/N): ").strip().lower() in ['y','yes']
    print("\nSummary:")
    print(f"Model: {selected_model}")
    print(f"Language: {selected_language}")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Formats: {selected_formats}")
    print(f"Overwrite: {overwrite}")
    confirm = input("Proceed? (Y/n): ").strip().lower()
    if confirm in ['n', 'no']:
        print("Cancelled.")
        return
    transcribe_files(input_dir, output_dir, selected_model, selected_language, selected_formats, overwrite)

def transcribe_files(input_dir, output_dir, model, language, formats, overwrite):
    worker = TranscriptionWorker()
    files = sorted(glob(f'{input_dir}/*'))
    audio_files = [f for f in files if worker.is_supported_file(f)]
    if not audio_files:
        print(f"No supported audio/video files found in: {input_dir}")
        return
    os.makedirs(output_dir, exist_ok=True)
    for i, file_path in enumerate(audio_files, 1):
        out_base = os.path.join(output_dir, Path(file_path).stem)
        skip = False
        for fmt in formats:
            out_file = f"{out_base}.{fmt}"
            if os.path.exists(out_file) and not overwrite:
                print(f"[{i}/{len(audio_files)}] Skipping {file_path} (exists)")
                skip = True
                break
        if skip:
            continue
        print(f"[{i}/{len(audio_files)}] Transcribing {file_path} ...")
        worker.transcribe(file_path, output_dir, model, language, formats)
        while worker.is_transcribing():
            pass
    print("Done.")

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio/video files using faster-whisper.")
    parser.add_argument('-i', '--input', help='Input directory with audio/video files')
    parser.add_argument('-o', '--output', help='Output directory for transcriptions')
    parser.add_argument('-m', '--model', choices=TranscriptionWorker.AVAILABLE_MODELS, help='Model size')
    parser.add_argument('-l', '--language', help='Language code')
    parser.add_argument('-f', '--formats', nargs='+', help='Output formats (e.g. txt json srt)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing outputs')
    parser.add_argument('--update', action='store_true', help='Update dependencies (pip install -r requirements.txt)')
    args = parser.parse_args()

    if args.update:
        print("Updating dependencies...")
        os.system('pip install -r requirements.txt')
        print("Update complete.")
        return

    # If no CLI args, use interactive mode
    if not any([args.input, args.output, args.model, args.language, args.formats]):
        interactive_mode()
    else:
        input_dir = args.input or str(Path.cwd())
        output_dir = args.output or str(Path.cwd())
        model = args.model or 'base'
        language = args.language or 'auto'
        formats = args.formats or ['txt','json','srt']
        overwrite = args.overwrite
        transcribe_files(input_dir, output_dir, model, language, formats, overwrite)

if __name__ == '__main__':
    main()
