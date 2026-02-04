"""
WhisperIT - Audio/Video Transcription GUI Application
A simple PyQt6-based graphical interface for transcribing audio and video files using OpenAI Whisper.
Supports background transcription with screen lock and system tray integration.
Allows transcribing multiple files simultaneously.
"""

import sys
import subprocess
import io
from pathlib import Path
from collections import deque
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QFileDialog,
    QTextEdit, QProgressBar, QMessageBox, QGroupBox, QFormLayout, QSystemTrayIcon, QMenu,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QObject

from transcriber import TranscriptionWorker, WHISPER_AVAILABLE


class StderrCapture(QObject):
    """Capture stderr and emit it as a signal."""
    output_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.buffer = io.StringIO()
    
    def write(self, message):
        """Write to buffer and emit signal."""
        if message and message.strip():
            self.output_signal.emit(f"[stderr] {message.strip()}")
        return self.buffer.write(message)
    
    def flush(self):
        """Flush the buffer."""
        return self.buffer.flush()
    
    def getvalue(self):
        """Get buffer value."""
        return self.buffer.getvalue()



class DragDropListWidget(QListWidget):
    """Custom QListWidget that supports drag-and-drop of files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
    
    def dragEnterEvent(self, event):
        """Accept drag events if they contain file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """Accept drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """Handle dropped files."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Emit custom signal with file paths
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.files_dropped.emit(file_paths)
        else:
            super().dropEvent(event)
    
    # Signal to emit when files are dropped
    files_dropped = pyqtSignal(list)


class TranscriptionThread(QThread):
    """Worker thread for transcription to keep GUI responsive and continue during screen lock."""
    progress_signal = pyqtSignal(str)
    file_progress_signal = pyqtSignal(str, str)  # file_path, message
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, worker, file_queue, output_dir, model, language, formats):
        super().__init__()
        self.worker = worker
        self.file_queue = file_queue
        self.output_dir = output_dir
        self.model = model
        self.language = language
        self.formats = formats
        self.prevent_sleep_process = None
        self.should_stop = False
    
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
            if len(self.file_queue) == 0:
                self.finished_signal.emit(False, "No files to transcribe")
                return
            
            self.progress_signal.emit(f"Starting transcription of {len(self.file_queue)} file(s)...")
            self.start_prevent_sleep()
            
            total_files = len(self.file_queue)
            completed = 0
            
            while len(self.file_queue) > 0 and not self.should_stop:
                file_path = self.file_queue.popleft()
                completed += 1
                
                self.file_progress_signal.emit(file_path, f"[{completed}/{total_files}] Processing: {Path(file_path).name}")
                
                try:
                    success = self.worker.transcribe(
                        file_path,
                        self.output_dir,
                        self.model,
                        self.language,
                        self.formats
                    )
                    
                    if success:
                        while self.worker.is_transcribing():
                            self.file_progress_signal.emit(file_path, f"[{completed}/{total_files}] ⏳ Transcribing: {Path(file_path).name}")
                            self.msleep(500)
                        
                        self.file_progress_signal.emit(file_path, f"[{completed}/{total_files}] ✓ Complete: {Path(file_path).name}")
                    else:
                        self.file_progress_signal.emit(file_path, f"[{completed}/{total_files}] ❌ Failed: {Path(file_path).name}")
                except Exception as e:
                    self.file_progress_signal.emit(file_path, f"[{completed}/{total_files}] ❌ Error: {str(e)}")
            
            if self.should_stop:
                self.finished_signal.emit(False, "Transcription queue stopped by user")
            else:
                self.progress_signal.emit(f"✓ All {completed} file(s) transcribed successfully!")
                self.finished_signal.emit(True, f"All files saved to: {self.output_dir}")
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")
        finally:
            self.stop_prevent_sleep()
    
    def stop_transcription(self):
        """Stop the transcription queue."""
        self.should_stop = True


class WhisperITGUI(QMainWindow):
    def __init__(self, stderr_capture=None):
        super().__init__()
        # Don't pass callback - threading issues with GUI updates from worker thread
        self.worker = TranscriptionWorker(status_callback=None)
        self.file_queue = deque()
        self.transcription_thread = None
        self.is_transcribing = False
        self.stderr_capture = stderr_capture
        
        # Setup system tray
        self.tray_icon = QSystemTrayIcon(self)
        self.setup_tray()
        
        self.init_ui()
        
        # Connect stderr capture if available
        if self.stderr_capture:
            self.stderr_capture.output_signal.connect(self.update_status)
        
        self.setWindowTitle("WhisperIT - Audio/Video Transcription")
        self.setGeometry(100, 100, 900, 900)
    
    def setup_tray(self):
        """Setup system tray icon and menu."""
        # Create a simple pixmap icon if no system icon is available
        from PyQt6.QtGui import QPixmap, QIcon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Draw a simple circle to represent the icon
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(70, 130, 180))  # Steel blue
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.showNormal)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def quit_app(self):
        """Quit the application."""
        if self.is_transcribing:
            reply = QMessageBox.question(
                self,
                "Confirm Quit",
                "Transcription in progress. Stop and quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes and self.transcription_thread:
                self.transcription_thread.stop_transcription()
                self.transcription_thread.wait()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        if self.is_transcribing:
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    def changeEvent(self, event):
        """Minimize to tray when window is minimized."""
        if event.type() == 3:  # WindowStateChange
            if self.isMinimized() and self.is_transcribing:
                self.hide()
    
    def init_ui(self):
        """Initialize the UI."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # File selection group
        main_layout.addWidget(self.create_file_selection())
        
        # Settings group
        main_layout.addWidget(self.create_settings_group())
        
        # Formats group
        main_layout.addWidget(self.create_formats_group())
        
        # Progress and status group
        main_layout.addWidget(self.create_progress_group())
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Transcription")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.start_btn.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Queue")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        self.stop_btn.clicked.connect(self.stop_transcription)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        main_widget.setLayout(main_layout)
    
    def create_file_selection(self):
        """Create file selection group."""
        group = QGroupBox("Step 1: Select Audio/Video Files")
        layout = QVBoxLayout()
        
        # Add files button
        file_layout = QHBoxLayout()
        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self.browse_files)
        file_layout.addWidget(add_files_btn)
        
        self.file_count_label = QLabel("No files selected")
        file_layout.addWidget(self.file_count_label)
        file_layout.addStretch()
        layout.addLayout(file_layout)
        
        # File list with drag-and-drop support
        self.file_list = DragDropListWidget()
        self.file_list.setMaximumHeight(150)
        self.file_list.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(QLabel("Selected files (or drag & drop):"))
        layout.addWidget(self.file_list)
        
        # Remove selected button
        remove_layout = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_files)
        remove_layout.addWidget(remove_btn)
        remove_layout.addStretch()
        layout.addLayout(remove_layout)
        
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
    
    def browse_files(self):
        """Browse for multiple audio/video files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio/Video Files",
            str(Path.home()),
            "Audio/Video Files (*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.mp4 *.mkv *.mov *.avi *.flv *.wmv *.webm);;All Files (*)"
        )
        if file_paths:
            self.add_files_to_queue(file_paths)
    
    def on_files_dropped(self, file_paths):
        """Handle files dropped onto the file list."""
        # Filter for supported formats
        supported = []
        for file_path in file_paths:
            path_obj = Path(file_path)
            # Check if it's a directory or a supported file
            if path_obj.is_dir():
                # Recursively add audio/video files from directory
                for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.webm']:
                    supported.extend(path_obj.glob(f'*{ext}'))
                    supported.extend(path_obj.glob(f'*{ext.upper()}'))
            elif path_obj.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv', '.webm']:
                supported.append(file_path)
        
        if supported:
            self.add_files_to_queue([str(f) for f in supported])
        else:
            QMessageBox.warning(self, "No Files", "No supported audio/video files found in the dropped items.")
    
    def add_files_to_queue(self, file_paths):
        """Add files to the queue and display list."""
        added_count = 0
        for file_path in file_paths:
            if file_path not in self.file_queue:
                self.file_queue.append(file_path)
                item = QListWidgetItem(Path(file_path).name)
                item.setData(256, file_path)  # Store full path in custom data
                self.file_list.addItem(item)
                added_count += 1
        
        if added_count > 0:
            self.update_file_count()
    
    def remove_selected_files(self):
        """Remove selected files from the queue."""
        for item in self.file_list.selectedItems():
            file_path = item.data(256)
            self.file_list.takeItem(self.file_list.row(item))
            if file_path in self.file_queue:
                self.file_queue.remove(file_path)
        
        self.update_file_count()
    
    def update_file_count(self):
        """Update the file count label."""
        count = len(self.file_queue)
        if count == 0:
            self.file_count_label.setText("No files selected")
        elif count == 1:
            self.file_count_label.setText("1 file selected")
        else:
            self.file_count_label.setText(f"{count} files selected")
    
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
        if len(self.file_queue) == 0:
            QMessageBox.warning(self, "Error", "Please select at least one audio/video file.")
            return
        
        output_dir = self.output_input.text()
        if not output_dir:
            QMessageBox.warning(self, "Error", "Please specify an output directory.")
            return
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get settings
        model = self.model_combo.currentText()
        language = self.language_combo.currentData()
        formats = self.get_selected_formats()
        
        # Disable button and show progress
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.is_transcribing = True
        
        # Create and start transcription thread
        self.transcription_thread = TranscriptionThread(
            self.worker,
            self.file_queue.copy(),
            output_dir,
            model,
            language,
            formats
        )
        self.transcription_thread.progress_signal.connect(self.update_status)
        self.transcription_thread.file_progress_signal.connect(self.update_file_status)
        self.transcription_thread.finished_signal.connect(self.on_transcription_finished)
        self.transcription_thread.start()
        
        # Show tray notification
        self.tray_icon.showMessage(
            "WhisperIT",
            f"Transcription of {len(self.file_queue)} file(s) started.\nApp can be minimized, closed, or screen locked.\nTranscription will continue in background.",
            QSystemTrayIcon.MessageIcon.Information,
            7000
        )
    
    def stop_transcription(self):
        """Stop the transcription queue."""
        if self.transcription_thread:
            self.transcription_thread.stop_transcription()
            self.update_status("⏹️ Stopping transcription queue...")
            self.stop_btn.setEnabled(False)
    
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
    
    def update_file_status(self, file_path, message):
        """Update status for a specific file."""
        self.update_status(message)
    
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
        self.file_list.clear()
        self.file_queue.clear()
        self.model_combo.setCurrentText('base')
        self.language_combo.setCurrentIndex(0)
        self.output_input.setText(str(Path.home() / 'Transcriptions'))
        self.txt_check.setChecked(True)
        self.json_check.setChecked(True)
        self.tsv_check.setChecked(True)
        self.status_text.clear()
        self.update_file_count()


def main():
    """Main entry point."""
    if not WHISPER_AVAILABLE:
        print("❌ ERROR: OpenAI Whisper not installed!")
        print("Please install it with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create stderr capture before creating the app
    stderr_capture = StderrCapture()
    original_stderr = sys.stderr
    
    app = QApplication(sys.argv)
    window = WhisperITGUI(stderr_capture=stderr_capture)
    
    # Redirect stderr after window is created (so signal connections work)
    sys.stderr = stderr_capture
    
    window.show()
    result = app.exec()
    
    # Restore stderr
    sys.stderr = original_stderr
    return result


if __name__ == "__main__":
    main()
