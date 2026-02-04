"""
WhisperIT - Audio/Video Transcription GUI Application
A simple PyQt6-based graphical interface for transcribing audio and video files using OpenAI Whisper.
Supports background transcription with screen lock and system tray integration.
"""

import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QFileDialog,
    QTextEdit, QProgressBar, QMessageBox, QGroupBox, QFormLayout, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont

from transcriber import TranscriptionWorker, WHISPER_AVAILABLE


class TranscriptionThread(QThread):
    """Worker thread for transcription to keep GUI responsive and continue during screen lock."""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, worker, file_path, output_dir, model, language, formats):
        super().__init__()
        self.worker = worker
        self.file_path = file_path
        self.output_dir = output_dir
        self.model = model
        self.language = language
        self.formats = formats
        self.prevent_sleep_process = None
    
    def start_prevent_sleep(self):
        """Start process to prevent macOS from sleeping."""
        try:
            # Use caffeinate on macOS to prevent sleep during transcription
            if sys.platform == 'darwin':
                self.prevent_sleep_process = subprocess.Popen(
                    ['caffeinate', '-i'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.progress_signal.emit("💤 Sleep prevention activated - transcription will continue even during screen lock")
        except Exception as e:
            self.progress_signal.emit(f"Note: Sleep prevention not available: {e}")
    
    def stop_prevent_sleep(self):
        """Stop the sleep prevention process."""
        if self.prevent_sleep_process:
            try:
                self.prevent_sleep_process.terminate()
                self.prevent_sleep_process.wait(timeout=2)
                self.progress_signal.emit("Sleep prevention stopped")
            except Exception as e:
                self.progress_signal.emit(f"Note: Could not stop sleep prevention: {e}")
    
    def run(self):
        try:
            self.progress_signal.emit("Starting transcription...")
            self.start_prevent_sleep()
            
            success = self.worker.transcribe(
                self.file_path,
                self.output_dir,
                self.model,
                self.language,
                self.formats
            )
            
            if success:
                while self.worker.is_transcribing():
                    self.progress_signal.emit("⏳ Transcription in progress...")
                    self.msleep(500)
                
                self.progress_signal.emit("✓ Transcription complete!")
                self.finished_signal.emit(True, f"Files saved to: {self.output_dir}")
            else:
                self.finished_signal.emit(False, "Failed to start transcription")
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")
        finally:
            self.stop_prevent_sleep()


class WhisperITGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = TranscriptionWorker(status_callback=self.update_status)
        self.transcription_thread = None
        self.is_transcribing = False
        
        # Setup system tray
        self.tray_icon = QSystemTrayIcon(self)
        self.setup_tray()
        
        self.init_ui()
        self.setWindowTitle("WhisperIT - Audio/Video Transcription")
        self.setGeometry(100, 100, 900, 800)
    
    def setup_tray(self):
        """Setup system tray icon and menu."""
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.showNormal)
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def changeEvent(self, event):
        """Handle window state changes."""
        if event.type() == 2:  # QEvent.WindowStateChange
            if self.isMinimized() and self.is_transcribing:
                self.hide()
                self.tray_icon.showMessage(
                    "WhisperIT",
                    "Transcription continues in background\n(Click tray icon to show window)",
                    QSystemTrayIcon.MessageIcon.Information,
                    5000
                )
                return
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_transcribing:
            reply = QMessageBox.question(
                self,
                "Transcription in Progress",
                "Transcription is still running. Close anyway?\n(Transcription will continue in background)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.hide()
                event.ignore()
            else:
                event.ignore()
        else:
            event.accept()
    
    def quit_app(self):
        """Quit the application."""
        if self.is_transcribing:
            reply = QMessageBox.question(
                self,
                "Transcription in Progress",
                "Transcription is still running. Really quit?\n(Transcription will be stopped)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        QApplication.quit()
    
    def init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🎙️  WhisperIT - Audio/Video Transcription")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Info label
        info_label = QLabel("Background transcription enabled - continues even during screen lock")
        info_font = QFont()
        info_font.setPointSize(9)
        info_font.setItalic(True)
        info_label.setFont(info_font)
        main_layout.addWidget(info_label)
        
        # File Selection
        file_group = self.create_file_selection()
        main_layout.addWidget(file_group)
        
        # Settings Group
        settings_group = self.create_settings_group()
        main_layout.addWidget(settings_group)
        
        # Output Formats Group
        formats_group = self.create_formats_group()
        main_layout.addWidget(formats_group)
        
        # Progress and Status
        progress_group = self.create_progress_group()
        main_layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Transcription")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.start_btn.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.start_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
    
    def create_file_selection(self):
        """Create file selection group."""
        group = QGroupBox("Step 1: Select Audio/Video File")
        layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select an audio or video file...")
        self.file_input.setReadOnly(True)
        file_layout.addWidget(self.file_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        group.setLayout(layout)
        return group
    
    def create_settings_group(self):
        """Create settings group."""
        group = QGroupBox("Step 2: Configure Settings")
        layout = QFormLayout()
        
        # Model selection
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
        self.model_combo.setCurrentText('base')
        layout.addRow(model_label, self.model_combo)
        
        # Language selection
        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItem('Auto-detect', 'auto')
        
        # Priority languages (most common)
        priority_langs = ['en', 'sv', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh']
        added = set()
        
        # Add priority languages first
        for code in priority_langs:
            if code in self.worker.LANGUAGES:
                name = self.worker.LANGUAGES[code]
                self.language_combo.addItem(f"{name} ({code})", code)
                added.add(code)
        
        # Add remaining languages
        for code, name in self.worker.LANGUAGES.items():
            if code not in added:
                self.language_combo.addItem(f"{name} ({code})", code)
                added.add(code)
                if len(added) >= 30:  # Limit to prevent huge dropdown
                    break
        
        layout.addRow(language_label, self.language_combo)
        
        # Output directory
        output_label = QLabel("Output Directory:")
        output_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        default_output = str(Path.home() / 'Transcriptions')
        self.output_input.setText(default_output)
        output_layout.addWidget(self.output_input)
        
        output_btn = QPushButton("Browse...")
        output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(output_btn)
        
        layout.addRow(output_label, output_layout)
        
        group.setLayout(layout)
        return group
    
    def create_formats_group(self):
        """Create output formats group."""
        group = QGroupBox("Step 3: Select Output Formats")
        layout = QHBoxLayout()
        
        self.txt_check = QCheckBox("TXT (Plain text)")
        self.txt_check.setChecked(True)
        layout.addWidget(self.txt_check)
        
        self.json_check = QCheckBox("JSON (Structured)")
        self.json_check.setChecked(True)
        layout.addWidget(self.json_check)
        
        self.tsv_check = QCheckBox("TSV (Timestamps)")
        self.tsv_check.setChecked(True)
        layout.addWidget(self.tsv_check)
        
        group.setLayout(layout)
        return group
    
    def create_progress_group(self):
        """Create progress and status group."""
        group = QGroupBox("Status")
        layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        layout.addWidget(self.status_text)
        
        group.setLayout(layout)
        return group
    
    def browse_file(self):
        """Browse for audio/video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio/Video File",
            str(Path.home()),
            "Audio/Video Files (*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.mp4 *.mkv *.mov *.avi *.flv *.wmv *.webm);;All Files (*)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def browse_output(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        if directory:
            self.output_input.setText(directory)
    
    def get_selected_formats(self):
        """Get selected output formats."""
        formats = []
        if self.txt_check.isChecked():
            formats.append('txt')
        if self.json_check.isChecked():
            formats.append('json')
        if self.tsv_check.isChecked():
            formats.append('tsv')
        return formats if formats else ['txt']
    
    def start_transcription(self):
        """Start the transcription process."""
        # Validate inputs
        file_path = self.file_input.text()
        if not file_path or not Path(file_path).exists():
            QMessageBox.warning(self, "Error", "Please select a valid audio/video file.")
            return
        
        output_dir = self.output_input.text()
        if not output_dir:
            QMessageBox.warning(self, "Error", "Please specify an output directory.")
            return
        
        # Get settings
        model = self.model_combo.currentText()
        language = self.language_combo.currentData()
        formats = self.get_selected_formats()
        
        # Disable button and show progress
        self.start_btn.setEnabled(False)
        self.status_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.is_transcribing = True
        
        # Create and start transcription thread
        self.transcription_thread = TranscriptionThread(
            self.worker,
            file_path,
            output_dir,
            model,
            language,
            formats
        )
        self.transcription_thread.progress_signal.connect(self.update_status)
        self.transcription_thread.finished_signal.connect(self.on_transcription_finished)
        self.transcription_thread.start()
        
        # Show tray notification
        self.tray_icon.showMessage(
            "WhisperIT",
            "Transcription started.\nApp can be minimized, closed, or screen locked.\nTranscription will continue in background.",
            QSystemTrayIcon.MessageIcon.Information,
            7000
        )
    
    def update_status(self, message):
        """Update status text."""
        current = self.status_text.toPlainText()
        if current:
            self.status_text.setText(current + "\n" + message)
        else:
            self.status_text.setText(message)
        # Auto-scroll to bottom
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def on_transcription_finished(self, success, message):
        """Handle transcription completion."""
        self.is_transcribing = False
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        
        if success:
            self.update_status(message)
            self.tray_icon.showMessage(
                "WhisperIT",
                f"✓ Transcription complete!\n{message}",
                QSystemTrayIcon.MessageIcon.Information,
                10000
            )
            # Show window if minimized
            if self.isMinimized():
                self.showNormal()
                self.activateWindow()
            QMessageBox.information(self, "Success", message)
        else:
            self.update_status(f"❌ {message}")
            self.tray_icon.showMessage(
                "WhisperIT",
                f"Error: {message}",
                QSystemTrayIcon.MessageIcon.Critical,
                10000
            )
            QMessageBox.critical(self, "Error", message)
    
    def clear_form(self):
        """Clear all form fields."""
        self.file_input.clear()
        self.model_combo.setCurrentText('base')
        self.language_combo.setCurrentIndex(0)
        self.output_input.setText(str(Path.home() / 'Transcriptions'))
        self.txt_check.setChecked(True)
        self.json_check.setChecked(True)
        self.tsv_check.setChecked(True)
        self.status_text.clear()


def main():
    """Main entry point."""
    if not WHISPER_AVAILABLE:
        print("❌ ERROR: OpenAI Whisper not installed!")
        print("Please install it with: pip install -r requirements.txt")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    window = WhisperITGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
