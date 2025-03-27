import os
import sys
import requests
import zipfile
import shutil
import platform
import winshell  # Added for Windows shortcut creation
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMessageBox, QMainWindow, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QWidget, 
                             QProgressBar, QLabel, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Configuration
GITHUB_ZIP_URL = "https://raw.githubusercontent.com/crtentertainment/CookieBatch/main/Official/CookieBatch.zip"
APP_NAME = "CookieBatch Installer"

# Temporary Paths
ZIP_PATH = os.path.join(os.getcwd(), "downloaded.zip")
EXTRACT_PATH = os.path.join(os.getcwd(), "extracted")

# Default Install Directory
DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "CookieBatch")

# Define global styling constants - DARK THEME
PRIMARY_COLOR = "#4a90e2"     # Blue
SECONDARY_COLOR = "#357abd"   # Darker blue
PRESSED_COLOR = "#2a5d8b"     # Even darker blue
ACCENT_COLOR = "#61dafb"      # Light blue for accents
BACKGROUND_COLOR = "#1e1e1e"  # Dark background
SECONDARY_BG_COLOR = "#2d2d2d"  # Slightly lighter background for inputs
BORDER_COLOR = "#3d3d3d"      # Border color
TEXT_COLOR = "#e0e0e0"        # Light text
DARKER_TEXT_COLOR = "#b0b0b0" # Slightly darker text for secondary info

# Input style
INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {SECONDARY_BG_COLOR};
        color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 5px;
        padding: 8px;
    }}
"""

# Button style
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {PRIMARY_COLOR};
        color: {TEXT_COLOR};
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {SECONDARY_COLOR};
    }}
    QPushButton:pressed {{
        background-color: {PRESSED_COLOR};
    }}
    QPushButton:disabled {{
        background-color: {BORDER_COLOR};
        color: {DARKER_TEXT_COLOR};
    }}
"""

# Progress Bar Style
PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: 2px solid {BORDER_COLOR};
        border-radius: 5px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {PRIMARY_COLOR};
        width: 10px;
        margin: 0.5px;
    }}
"""

class DownloadThread(QThread):
    """Thread to handle file download with progress updates."""
    progress_updated = pyqtSignal(int)
    download_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            # Send a GET request to the URL
            response = requests.get(self.url, stream=True)
            response.raise_for_status()

            # Get the total file size
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte
            downloaded_size = 0

            # Open the file and write downloaded content
            with open(self.save_path, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded_size += len(data)
                    
                    # Calculate and emit progress
                    if total_size > 0:
                        progress = int((downloaded_size / total_size) * 100)
                        self.progress_updated.emit(progress)

            # Emit download complete signal
            self.download_complete.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

class Installer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(500, 450)  # Slightly taller to accommodate new checkbox
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        
        # Title with larger font
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("CookieBatch Installer")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {ACCENT_COLOR};")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_font = QFont("Arial", 12)
        subtitle_label = QLabel("Python Batch Code Obfuscator Deployment")
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {TEXT_COLOR};")
        main_layout.addWidget(subtitle_label)
        
        main_layout.addSpacing(30)
        
        # Installation path selection
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select Installation Directory")
        self.path_input.setReadOnly(True)
        self.path_input.setStyleSheet(INPUT_STYLE)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setStyleSheet(BUTTON_STYLE)
        self.browse_button.clicked.connect(self.select_install_path)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        
        main_layout.addLayout(path_layout)
        
        # Shortcut creation checkbox
        self.create_shortcut_checkbox = QCheckBox("Create Desktop Shortcut")
        self.create_shortcut_checkbox.setStyleSheet(f"color: {TEXT_COLOR};")
        self.create_shortcut_checkbox.setChecked(True)
        main_layout.addWidget(self.create_shortcut_checkbox)
        
        # Install button
        self.install_button = QPushButton("Install")
        self.install_button.setMinimumHeight(50)
        self.install_button.setStyleSheet(BUTTON_STYLE)
        self.install_button.setEnabled(True)
        self.install_button.clicked.connect(self.start_installation)
        main_layout.addWidget(self.install_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to install")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {DARKER_TEXT_COLOR};")
        main_layout.addWidget(self.status_label)
        
        # Version info
        version_label = QLabel("Installer v1.1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet(f"color: {DARKER_TEXT_COLOR};")
        main_layout.addWidget(version_label)
        
        # Set up container
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Set default install directory
        self.install_dir = DEFAULT_INSTALL_DIR
        self.path_input.setText(self.install_dir)
        self.status_label.setText(f"Ready to install to: {self.install_dir}")

    def select_install_path(self):
        """Opens a dialog to select an installation directory."""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select CookieBatch Installation Folder", 
            self.install_dir  # Start in the default directory
        )
        if path:
            self.install_dir = path
            self.path_input.setText(path)
            self.status_label.setText(f"Ready to install to: {path}")

    def create_desktop_shortcut(self, install_path):
        """Create desktop shortcut for the application."""
        try:
            # Find the main script or executable
            possible_scripts = [
                os.path.join(install_path, "CookieBatch.exe"),
            ]
            
            script_path = None
            for script in possible_scripts:
                if os.path.exists(script):
                    script_path = script
                    break
            
            if not script_path:
                # Check for any Python script in the directory
                for file in os.listdir(install_path):
                    if file.endswith('.py'):
                        script_path = os.path.join(install_path, file)
                        break
            
            if not script_path:
                raise ValueError("No Python script found in the installation directory")
            
            # Use winshell to create desktop shortcut on Windows
            desktop = winshell.desktop()
            path = os.path.join(desktop, "CookieBatch.lnk")
            
            # Use python executable to run the script
            python_exe = sys.executable
            
            winshell.CreateShortcut(
                Path=path,
                Target=python_exe,
                Arguments=f'"{script_path}"',
                Icon=(script_path, 0),
                Description="CookieBatch - Python Batch Code Obfuscator"
            )
            
            return True
        except Exception as e:
            QMessageBox.warning(self, "Shortcut Creation Warning", 
                                f"Could not create desktop shortcut: {e}")
            return False

    def start_installation(self):
        """Start the installation process."""
        # Disable buttons during installation
        self.install_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Start download thread
        self.download_thread = DownloadThread(GITHUB_ZIP_URL, ZIP_PATH)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.download_complete.connect(self.on_download_complete)
        self.download_thread.error_occurred.connect(self.on_installation_error)
        
        # Update status and start download
        self.status_label.setText("Downloading files...")
        self.download_thread.start()

    def update_progress(self, value):
        """Update progress bar during download."""
        self.progress_bar.setValue(value)

    def on_download_complete(self):
        """Handle successful download and start extraction."""
        try:
            self.status_label.setText("Extracting files...")
            
            if not zipfile.is_zipfile(ZIP_PATH):
                raise ValueError("Downloaded file is not a valid ZIP archive.")

            # Extract files with progress
            with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
                total_files = len(zip_ref.namelist())
                for i, file in enumerate(zip_ref.namelist(), 1):
                    zip_ref.extract(file, EXTRACT_PATH)
                    # Update progress based on file extraction
                    self.progress_bar.setValue(int((i / total_files) * 100))

            if not os.listdir(EXTRACT_PATH):
                raise ValueError("Extraction failed: No files found.")

            # Create install directory
            os.makedirs(self.install_dir, exist_ok=True)

            # Move extracted files
            for item in os.listdir(EXTRACT_PATH):
                src = os.path.join(EXTRACT_PATH, item)
                dest = os.path.join(self.install_dir, item)

                if os.path.exists(dest):
                    if os.path.isdir(dest):
                        shutil.rmtree(dest)
                    else:
                        os.remove(dest)

                shutil.move(src, dest)

            # Clean up temporary files
            os.remove(ZIP_PATH)
            shutil.rmtree(EXTRACT_PATH)

            # Create desktop shortcut if checkbox is checked
            shortcut_created = False
            if self.create_shortcut_checkbox.isChecked():
                # Only create shortcut on Windows
                if platform.system() == "Windows":
                    shortcut_created = self.create_desktop_shortcut(self.install_dir)

            # Final status update
            self.status_label.setText("Installation completed successfully!")
            self.progress_bar.setValue(100)
            
            # Prepare completion message
            message = f"CookieBatch installed successfully in:\n{self.install_dir}"
            if shortcut_created:
                message += "\n\nDesktop shortcut created."
            
            QMessageBox.information(self, "Installation Complete", message)

        except Exception as e:
            self.on_installation_error(str(e))

    def on_installation_error(self, error_message):
        """Handle any errors during installation."""
        QMessageBox.critical(self, "Installation Error", 
                             f"Installation failed: {error_message}")
        self.status_label.setText("Installation failed")
        self.progress_bar.setValue(0)
        
        # Re-enable buttons
        self.install_button.setEnabled(True)
        self.browse_button.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern, cross-platform styling
    
    # Set global font to Arial
    app.setFont(QFont("Arial", 10))
    
    window = Installer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()