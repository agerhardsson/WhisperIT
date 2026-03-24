"""
Transcription Worker Module
Handles the transcription logic, threading, and output generation.
"""

import os
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class TranscriptionWorker:
    """
    Handles transcription tasks in a separate thread.
    Manages status updates and output file generation.
    """
    
    # Supported audio/video formats
    SUPPORTED_FORMATS = {
        'audio': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'],
        'video': ['.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.webm']
    }
    
    # Available models
    AVAILABLE_MODELS = ['tiny', 'base', 'small', 'medium', 'large']
    
    # Supported languages (ISO 639-1 codes with names)
    LANGUAGES = {
        'auto': 'Auto-detect',
        'af': 'Afrikaans',
        'ar': 'Arabic',
        'hy': 'Armenian',
        'az': 'Azerbaijani',
        'be': 'Belarusian',
        'bs': 'Bosnian',
        'bg': 'Bulgarian',
        'ca': 'Catalan',
        'ceb': 'Cebuano',
        'zh': 'Chinese',
        'cs': 'Czech',
        'cy': 'Welsh',
        'da': 'Danish',
        'de': 'German',
        'el': 'Greek',
        'en': 'English',
        'es': 'Spanish',
        'et': 'Estonian',
        'fa': 'Persian',
        'fi': 'Finnish',
        'fr': 'French',
        'gl': 'Galician',
        'ka': 'Georgian',
        'he': 'Hebrew',
        'hi': 'Hindi',
        'hu': 'Hungarian',
        'is': 'Icelandic',
        'id': 'Indonesian',
        'it': 'Italian',
        'ja': 'Japanese',
        'jv': 'Javanese',
        'kn': 'Kannada',
        'kk': 'Kazakh',
        'km': 'Khmer',
        'ko': 'Korean',
        'la': 'Latin',
        'lv': 'Latvian',
        'lt': 'Lithuanian',
        'mk': 'Macedonian',
        'mg': 'Malagasy',
        'ms': 'Malay',
        'ml': 'Malayalam',
        'mt': 'Maltese',
        'mi': 'Māori',
        'mr': 'Marathi',
        'mn': 'Mongolian',
        'ne': 'Nepali',
        'nl': 'Dutch',
        'no': 'Norwegian',
        'oc': 'Occitan',
        'pa': 'Punjabi',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'ro': 'Romanian',
        'ru': 'Russian',
        'sa': 'Sanskrit',
        'sr': 'Serbian',
        'sk': 'Slovak',
        'sl': 'Slovenian',
        'so': 'Somali',
        'sv': 'Swedish',
        'sw': 'Swahili',
        'ta': 'Tamil',
        'te': 'Telugu',
        'th': 'Thai',
        'tl': 'Tagalog',
        'tr': 'Turkish',
        'tk': 'Turkmen',
        'uk': 'Ukrainian',
        'ur': 'Urdu',
        'uz': 'Uzbek',
        'vi': 'Vietnamese',
        'yo': 'Yoruba',
    }
    
    def __init__(self, status_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the transcription worker.
        
        Args:
            status_callback: Function to call with status updates
        """
        self.status_callback = status_callback
        self.is_running = False
        self.current_thread: Optional[threading.Thread] = None
        
        if not WHISPER_AVAILABLE:
            self._update_status("ERROR: OpenAI Whisper not installed. Run: pip install -r requirements.txt")
    
    def _update_status(self, message: str):
        """Update status via callback if available."""
        if self.status_callback:
            self.status_callback(message)
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file format is supported for transcription."""
        ext = Path(file_path).suffix.lower()
        all_formats = self.SUPPORTED_FORMATS['audio'] + self.SUPPORTED_FORMATS['video']
        return ext in all_formats
    
    @staticmethod
    def format_timestamp(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    
    def transcribe(self, file_path: str, output_dir: str, model: str = 'base',
                   language: str = 'auto', output_formats: list = None) -> bool:
        """
        Start transcription in a background thread.
        
        Args:
            file_path: Path to audio/video file
            output_dir: Directory to save output files
            model: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            language: Language code (ISO 639-1) or 'auto' for auto-detection
            output_formats: List of output formats ['txt', 'json', 'tsv', 'srt']
        
        Returns:
            True if transcription started successfully
        """
        if not WHISPER_AVAILABLE:
            self._update_status("ERROR: OpenAI Whisper not installed")
            return False
        
        if not os.path.exists(file_path):
            self._update_status(f"ERROR: File not found: {file_path}")
            return False
        
        if not self.is_supported_file(file_path):
            self._update_status("ERROR: Unsupported file format")
            return False
        
        if output_formats is None:
            output_formats = ['txt', 'json', 'tsv', 'srt']
        
        # Stop any existing transcription
        if self.is_running:
            self.stop()
        
        # Start transcription in background thread
        self.is_running = True
        self.current_thread = threading.Thread(
            target=self._transcribe_worker,
            args=(file_path, output_dir, model, language, output_formats),
            daemon=False
        )
        self.current_thread.start()
        self._update_status(f"Starting transcription of {Path(file_path).name}...")
        
        return True
    
    def _transcribe_worker(self, file_path: str, output_dir: str, model: str,
                          language: str, output_formats: list):
        """Background worker thread for transcription."""
        try:
            self._update_status(f"Loading model '{model}'...")
            
            # Load the faster-whisper model
            whisper_model = WhisperModel(model, device="auto", compute_type="auto")
            self._update_status("Model loaded. Processing audio...")
            
            # Prepare language parameter
            language_param = None if language == 'auto' else language
            
            # Run transcription with faster-whisper
            segments, info = whisper_model.transcribe(
                audio=file_path,
                language=language_param,
                beam_size=5,
                best_of=5
            )
            
            if not self.is_running:
                return
            
            # Convert segments generator to list and build result dict
            segments_list = list(segments)
            result = {
                'text': ' '.join([segment.text for segment in segments_list]),
                'language': info.language,
                'duration': info.duration,
                'segments': [
                    {
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text.strip()
                    }
                    for segment in segments_list
                ]
            }
            
            self._update_status("Generating output files...")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output file paths
            input_filename = Path(file_path).stem
            output_paths = {}
            
            # Save transcription in requested formats
            if 'txt' in output_formats:
                txt_file = os.path.join(output_dir, f"{input_filename}.txt")
                self._save_txt(result, txt_file)
                output_paths['txt'] = txt_file
                self._update_status(f"✓ Saved: {Path(txt_file).name}")
            
            if 'json' in output_formats:
                json_file = os.path.join(output_dir, f"{input_filename}.json")
                self._save_json(result, json_file)
                output_paths['json'] = json_file
                self._update_status(f"✓ Saved: {Path(json_file).name}")
            
            if 'tsv' in output_formats:
                tsv_file = os.path.join(output_dir, f"{input_filename}.tsv")
                self._save_tsv(result, tsv_file)
                output_paths['tsv'] = tsv_file
                self._update_status(f"✓ Saved: {Path(tsv_file).name}")
            
            if 'srt' in output_formats:
                srt_file = os.path.join(output_dir, f"{input_filename}.srt")
                self._save_srt(result, srt_file)
                output_paths['srt'] = srt_file
                self._update_status(f"✓ Saved: {Path(srt_file).name}")
            
            # Save summary JSON
            summary_file = os.path.join(output_dir, f"{input_filename}_summary.json")
            self._save_summary(result, file_path, model, language, output_paths, summary_file)
            self._update_status(f"✓ Saved: {Path(summary_file).name}")
            
            self._update_status("✓ Finished!")
            self.is_running = False
            
        except Exception as e:
            self._update_status(f"ERROR: {str(e)}")
            self.is_running = False
    
    @staticmethod
    def _save_txt(result: Dict[str, Any], output_file: str):
        """Save transcription as plain text."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['text'].strip())
    
    @staticmethod
    def _save_json(result: Dict[str, Any], output_file: str):
        """Save transcription with segments as JSON."""
        output_data = {
            'text': result['text'],
            'language': result.get('language', 'unknown'),
            'segments': result.get('segments', [])
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _save_tsv(result: Dict[str, Any], output_file: str):
        """Save transcription with timestamps as TSV."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("start\tend\ttext\n")
            for segment in result.get('segments', []):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').strip()
                f.write(f"{start:.2f}\t{end:.2f}\t{text}\n")
    
    @staticmethod
    def _save_srt(result: Dict[str, Any], output_file: str):
        """Save transcription as SRT subtitle file."""
        segments = result.get('segments', [])
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start = TranscriptionWorker.format_timestamp(segment.get('start', 0))
                end = TranscriptionWorker.format_timestamp(segment.get('end', 0))
                text = segment.get('text', '').strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    
    @staticmethod
    def _save_summary(result: Dict[str, Any], input_file: str, model: str,
                     language: str, output_paths: Dict[str, str], summary_file: str):
        """Save summary JSON with metadata."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'input_file': os.path.basename(input_file),
            'model': model,
            'language': language,
            'detected_language': result.get('language', 'unknown'),
            'duration_seconds': result.get('duration', 0),
            'output_files': output_paths,
            'text_preview': result['text'][:200] + ('...' if len(result['text']) > 200 else '')
        }
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def stop(self):
        """Stop the current transcription."""
        self.is_running = False
        self._update_status("Stopping transcription...")
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=5)
    
    def is_transcribing(self) -> bool:
        """Check if transcription is currently running."""
        return self.is_running
