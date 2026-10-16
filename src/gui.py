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
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, QScrollArea, QStyle
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QObject, QSettings
from huggingface_hub import snapshot_download, try_to_load_from_cache
from tqdm.auto import tqdm

from .transcriber import TranscriptionWorker, WHISPER_AVAILABLE


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
    progress_bar_signal = pyqtSignal(int, int)  # current, total
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
                
                # Update progress bar
                self.progress_bar_signal.emit(completed, total_files)
                self.file_progress_signal.emit(file_path, f"Processing: {Path(file_path).name}")
                
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
                            self.msleep(500)
                        
                        self.file_progress_signal.emit(file_path, f"✓ Complete: {Path(file_path).name}")
                    else:
                        self.file_progress_signal.emit(file_path, f"❌ Failed: {Path(file_path).name}")
                except Exception as e:
                    self.file_progress_signal.emit(file_path, f"❌ Error: {str(e)}")
            
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


class ModelDownloadThread(QThread):
    finished_signal = pyqtSignal(str, bool, str)
    progress_signal = pyqtSignal(str, int, int)

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        repo_id = f"Systran/faster-whisper-{self.model}"

        thread = self

        class DownloadProgress(tqdm):
            def __init__(self, *args, **kwargs):
                kwargs["file"] = io.StringIO()
                kwargs["disable"] = False
                super().__init__(*args, **kwargs)

            def update(self, n=1):
                result = super().update(n)
                thread.progress_signal.emit(self.desc or "Downloading model files", self.n, self.total or 0)
                return result

        try:
            snapshot_download(repo_id=repo_id, tqdm_class=DownloadProgress)
            self.finished_signal.emit(self.model, True, "Model downloaded and ready")
        except Exception as error:
            self.finished_signal.emit(self.model, False, str(error))


class WhisperITGUI(QMainWindow):
    MODEL_SIZES = {
        "tiny": "~80 MB",
        "base": "~140 MB",
        "small": "~460 MB",
        "medium": "~1.5 GB",
        "large": "~2.9 GB",
    }

    def __init__(self, stderr_capture=None):
        super().__init__()
        # Don't pass callback - threading issues with GUI updates from worker thread
        self.worker = TranscriptionWorker(status_callback=None)
        self.file_queue = deque()
        self.transcription_thread = None
        self.is_transcribing = False
        self.stderr_capture = stderr_capture
        self.model_download_thread = None
        self.downloading_model = None
        self.start_after_download = False
        self.selected_model = "base"
        self.settings = QSettings("WhisperIT", "WhisperIT")
        self.theme = self.settings.value("theme", "system")
        if self.theme not in ("system", "light", "dark"):
            self.theme = "system"
        self.is_dark_theme = False
        self.model_radios = {}
        self.model_status_labels = {}
        self.model_download_buttons = {}
        self.model_downloaded = {
            model: self.is_model_downloaded(model)
            for model in TranscriptionWorker.AVAILABLE_MODELS
        }
        
        # Setup system tray
        self.tray_icon = QSystemTrayIcon(self)
        self.setup_tray()
        
        self.init_ui()
        
        # Connect stderr capture if available
        if self.stderr_capture:
            self.stderr_capture.output_signal.connect(self.update_status)
        
        self.setWindowTitle("WhisperIT - Audio/Video Transcription")
        self.setMinimumSize(680, 720)
        self.resize(880, 900)
    
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
        if self.is_transcribing or self.downloading_model is not None:
            reply = QMessageBox.question(
                self,
                "Confirm Quit",
                "A background task is in progress. Quit after it stops? Model downloads cannot currently be canceled.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            if self.transcription_thread and self.transcription_thread.isRunning():
                self.transcription_thread.stop_transcription()
                self.transcription_thread.wait()
            if self.model_download_thread and self.model_download_thread.isRunning():
                self.model_download_thread.wait()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        if self.is_transcribing or self.downloading_model is not None:
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
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 18, 20, 16)
        main_layout.setSpacing(14)

        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("WhisperIT")
        title.setObjectName("appTitle")
        subtitle = QLabel("Transcribe audio and video, privately on your device.")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        header.addStretch()
        theme_label = QLabel("Appearance")
        theme_label.setObjectName("themeLabel")
        header.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeSelector")
        self.theme_combo.addItem("System", "system")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(self.theme))
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        header.addWidget(self.theme_combo)
        main_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 8, 2)
        content_layout.setSpacing(12)
        content_layout.addWidget(self.create_file_selection())
        content_layout.addWidget(self.create_model_library())
        content_layout.addWidget(self.create_settings_group())
        content_layout.addWidget(self.create_formats_group())
        content_layout.addWidget(self.create_progress_group())
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

        button_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        self.start_btn = QPushButton("Start Transcription")
        self.start_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self.stop_transcription)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        main_layout.addLayout(button_layout)

        self.apply_theme()

    def change_theme(self):
        self.theme = self.theme_combo.currentData()
        self.settings.setValue("theme", self.theme)
        self.apply_theme()

    def on_system_palette_changed(self, _palette):
        if self.theme == "system":
            self.apply_theme()

    def apply_theme(self):
        system_dark = QApplication.palette().color(self.backgroundRole()).lightness() < 128
        self.is_dark_theme = system_dark if self.theme == "system" else self.theme == "dark"
        if self.is_dark_theme:
            colors = {
                "window": "#171c22", "surface": "#202830", "input": "#151b21",
                "text": "#e7edf1", "muted": "#a7b4be", "border": "#3b4852",
                "hover": "#303c45", "selection": "#285b58", "accent": "#21a69c",
                "accent_hover": "#18877f", "disabled": "#697780", "warning": "#e5ae68",
                "danger_bg": "#3b2828", "danger_text": "#ffb6aa", "progress": "#313b43",
            }
        else:
            colors = {
                "window": "#f4f6f8", "surface": "#ffffff", "input": "#ffffff",
                "text": "#18212b", "muted": "#5c6b78", "border": "#d3dce2",
                "hover": "#dfe8ed", "selection": "#b9e5df", "accent": "#087e78",
                "accent_hover": "#066b66", "disabled": "#8b969e", "warning": "#8a561a",
                "danger_bg": "#fff4f2", "danger_text": "#9c3333", "progress": "#e5ebef",
            }
        self.setStyleSheet(f"""
            QWidget {{ color: {colors['text']}; font-size: 13px; }}
            QMainWindow {{ background: {colors['window']}; }}
            QLabel#appTitle {{ font-size: 25px; font-weight: 700; color: {colors['text']}; }}
            QLabel#subtitle, QLabel#themeLabel {{ color: {colors['muted']}; font-size: 13px; }}
            QGroupBox {{
                background: {colors['surface']}; border: 1px solid {colors['border']}; border-radius: 10px;
                margin-top: 10px; padding: 12px; font-weight: 650; color: {colors['text']};
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; }}
            QPushButton {{
                background: {colors['surface']}; border: 1px solid {colors['border']}; border-radius: 7px;
                padding: 8px 12px; min-height: 20px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {colors['hover']}; }}
            QPushButton:disabled {{ color: {colors['disabled']}; background: {colors['window']}; }}
            QPushButton#primaryButton {{ color: white; background: {colors['accent']}; border-color: {colors['accent']}; }}
            QPushButton#primaryButton:hover {{ background: {colors['accent_hover']}; }}
            QPushButton#dangerButton {{ color: {colors['danger_text']}; background: {colors['danger_bg']}; border-color: {colors['border']}; }}
            QPushButton#dangerButton:hover {{ background: {colors['hover']}; }}
            QPushButton#secondaryButton {{ background: transparent; }}
            QLineEdit, QComboBox, QListWidget, QTextEdit {{
                color: {colors['text']}; background: {colors['input']};
                border: 1px solid {colors['border']}; border-radius: 6px; padding: 7px;
                selection-background-color: {colors['selection']}; selection-color: {colors['text']};
            }}
            QComboBox QAbstractItemView {{ color: {colors['text']}; background: {colors['surface']};
                selection-color: {colors['text']}; selection-background-color: {colors['selection']};
                border: 1px solid {colors['border']}; outline: 0; }}
            QRadioButton {{ spacing: 8px; font-weight: 650; }}
            QRadioButton::indicator {{ width: 17px; height: 17px; border-radius: 9px;
                border: 2px solid {colors['muted']}; background: {colors['input']}; }}
            QRadioButton::indicator:checked {{ border: 5px solid {colors['accent']}; background: {colors['input']}; }}
            QCheckBox {{ spacing: 7px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px;
                border: 2px solid {colors['muted']}; background: {colors['input']}; }}
            QCheckBox::indicator:hover {{ border-color: {colors['accent']}; }}
            QCheckBox::indicator:checked {{ background: {colors['accent']}; border-color: {colors['accent']}; }}
            QProgressBar {{ border: 0; border-radius: 4px; background: {colors['progress']}; min-height: 8px; max-height: 8px; }}
            QProgressBar::chunk {{ border-radius: 4px; background: {colors['accent']}; }}
            QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QPushButton:focus, QLineEdit:focus, QComboBox:focus, QListWidget:focus, QCheckBox:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        for label in self.findChildren(QLabel):
            if label.objectName() in ("modelSizeLabel", "modelDownloadMessage"):
                label.setStyleSheet(f"color: {colors['muted']};")
        if hasattr(self, "model_status_labels"):
            self.update_model_statuses()

    @staticmethod
    def is_model_downloaded(model):
        repo_id = f"Systran/faster-whisper-{model}"
        required_files = ("config.json", "model.bin")
        return all(
            isinstance(path, str) and Path(path).is_file()
            for path in (
                try_to_load_from_cache(repo_id, filename)
                for filename in required_files
            )
        )

    def create_model_library(self):
        group = QGroupBox("Choose a speech model")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        self.model_button_group = QButtonGroup(self)
        self.model_button_group.setExclusive(True)

        for model in TranscriptionWorker.AVAILABLE_MODELS:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            radio = QRadioButton(model.title())
            radio.setChecked(model == "base")
            radio.toggled.connect(lambda checked, name=model: self.select_model(name, checked))
            self.model_button_group.addButton(radio)
            self.model_radios[model] = radio
            row_layout.addWidget(radio)

            size_label = QLabel(self.MODEL_SIZES[model])
            size_label.setObjectName("modelSizeLabel")
            size_label.setMinimumWidth(75)
            row_layout.addWidget(size_label)

            status = QLabel()
            status.setMinimumWidth(110)
            status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.model_status_labels[model] = status
            row_layout.addWidget(status)

            download = QPushButton("Download")
            download.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
            download.setObjectName("secondaryButton")
            download.clicked.connect(lambda checked=False, name=model: self.download_model(name))
            self.model_download_buttons[model] = download
            row_layout.addWidget(download)
            layout.addWidget(row)

        self.model_progress = QProgressBar()
        self.model_progress.setRange(0, 0)
        self.model_progress.setVisible(False)
        layout.addWidget(self.model_progress)
        self.model_download_message = QLabel("")
        self.model_download_message.setObjectName("modelDownloadMessage")
        self.model_download_message.setVisible(False)
        layout.addWidget(self.model_download_message)
        self.update_model_statuses()
        group.setLayout(layout)
        return group

    def select_model(self, model, checked):
        if checked:
            self.selected_model = model

    def update_model_statuses(self):
        downloaded_color = "#51c4b8" if self.is_dark_theme else "#087e78"
        unavailable_color = "#e5ae68" if self.is_dark_theme else "#8a561a"
        for model, label in self.model_status_labels.items():
            downloading = model == self.downloading_model
            downloaded = self.model_downloaded.get(model, False)
            label.setText("Downloading…" if downloading else "Downloaded" if downloaded else "Not downloaded")
            label.setStyleSheet(
                f"color: {downloaded_color}; font-weight: 650;" if downloaded
                else f"color: {unavailable_color}; font-weight: 600;" if not downloading
                else f"color: {downloaded_color}; font-weight: 600;"
            )
            button = self.model_download_buttons[model]
            button.setText("Ready" if downloaded else "Downloading…" if downloading else "Download")
            button.setEnabled(
                not downloaded and not downloading
                and self.downloading_model is None and not self.is_transcribing
            )
        if hasattr(self, "model_progress"):
            self.model_progress.setVisible(self.downloading_model is not None)
    
    def create_file_selection(self):
        """Create file selection group."""
        group = QGroupBox("Step 1: Select Audio/Video Files")
        layout = QVBoxLayout()
        
        # Add files button
        file_layout = QHBoxLayout()
        add_files_btn = QPushButton("Add files")
        add_files_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        add_files_btn.setObjectName("secondaryButton")
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
        remove_btn = QPushButton("Remove selected")
        remove_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        remove_btn.setObjectName("secondaryButton")
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
        output_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        output_btn.setObjectName("secondaryButton")
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
        
        self.srt_check = QCheckBox("SRT (Subtitles)")
        self.srt_check.setChecked(True)
        layout.addWidget(self.srt_check)
        
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

    def download_model(self, model):
        if self.downloading_model is not None or self.is_transcribing:
            return
        self.downloading_model = model
        self.update_model_statuses()
        self.update_status(f"Downloading the {model} model. This may take several minutes...")
        self.model_download_thread = ModelDownloadThread(model)
        self.model_download_thread.progress_signal.connect(self.update_model_download_progress)
        self.model_download_thread.finished_signal.connect(self.on_model_download_finished)
        self.model_download_thread.start()

    def update_model_download_progress(self, description, current, total):
        self.model_download_message.setVisible(True)
        self.model_download_message.setText(description)
        if total > 0:
            self.model_progress.setRange(0, total)
            self.model_progress.setValue(current)
        else:
            self.model_progress.setRange(0, 0)

    def on_model_download_finished(self, model, success, message):
        self.downloading_model = None
        self.model_download_message.setVisible(False)
        self.model_progress.setRange(0, 0)
        self.model_downloaded[model] = success and self.is_model_downloaded(model)
        self.update_model_statuses()
        resume_transcription = self.start_after_download and self.selected_model == model
        self.start_after_download = False
        if self.model_downloaded[model]:
            self.update_status(f"{model.title()} model is downloaded and ready.")
            if resume_transcription:
                self.start_transcription()
        else:
            self.update_status(f"Could not download {model}: {message}")
            QMessageBox.warning(self, "Model download failed", message)

    
    def get_selected_formats(self):
        """Get selected output formats."""
        formats = []
        if self.txt_check.isChecked():
            formats.append('txt')
        if self.json_check.isChecked():
            formats.append('json')
        if self.tsv_check.isChecked():
            formats.append('tsv')
        if self.srt_check.isChecked():
            formats.append('srt')
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

        model = self.selected_model
        if self.downloading_model is not None:
            if self.downloading_model == model:
                self.start_after_download = True
                self.update_status(f"Transcription will start when the {model} model finishes downloading.")
            else:
                QMessageBox.information(self, "Model download in progress", "Wait for the current model download to finish before starting transcription.")
            return

        if not self.model_downloaded.get(model, False):
            reply = QMessageBox.question(
                self,
                "Model required",
                f"The {model} model ({self.MODEL_SIZES[model]}) is not downloaded. Download it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.start_after_download = True
                self.download_model(model)
            return
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get settings
        language = self.language_combo.currentData()
        formats = self.get_selected_formats()
        
        # Disable button and show progress
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.is_transcribing = True
        self.update_model_statuses()
        
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
        self.transcription_thread.progress_bar_signal.connect(self.update_progress_bar)
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
    
    def update_progress_bar(self, current, total):
        """Update progress bar with current/total files."""
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{current}/{total} files ({percentage}%)")
    
    def on_transcription_finished(self, success, message):
        """Handle transcription completion."""
        self.is_transcribing = False
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.update_model_statuses()
        
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
        self.model_radios['base'].setChecked(True)
        self.language_combo.setCurrentIndex(0)
        self.output_input.setText(str(Path.home() / 'Transcriptions'))
        self.txt_check.setChecked(True)
        self.json_check.setChecked(True)
        self.tsv_check.setChecked(True)
        self.srt_check.setChecked(True)
        self.status_text.clear()
        self.update_file_count()


def main():
    """Main entry point."""
    if not WHISPER_AVAILABLE:
        print("ERROR: faster-whisper is not installed.")
        print("Install dependencies with: uv sync")
        sys.exit(1)
    
    # Create stderr capture before creating the app
    stderr_capture = StderrCapture()
    original_stderr = sys.stderr
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WhisperITGUI(stderr_capture=stderr_capture)
    app.paletteChanged.connect(window.on_system_palette_changed)
    
    # Redirect stderr after window is created (so signal connections work)
    sys.stderr = stderr_capture
    
    window.show()
    result = app.exec()
    
    # Restore stderr
    sys.stderr = original_stderr
    return result


if __name__ == "__main__":
    main()
