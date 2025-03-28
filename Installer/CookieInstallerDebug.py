import os
import sys
import requests
import zipfile
import shutil
import platform
import winshell  # Added for Windows shortcut creation
import ctypes
import tempfile
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMessageBox, QMainWindow, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QWidget, 
                             QProgressBar, QLabel, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

# Configuration
GITHUB_ZIP_URL = "https://raw.githubusercontent.com/crtentertainment/CookieBatch/main/Official/CookieBatch.zip"
APP_NAME = "CookieBatch Installer"

# Use temporary directory for downloads to avoid permission issues
TEMP_DIR = tempfile.gettempdir()
ZIP_PATH = os.path.join(TEMP_DIR, "cookiebatch_downloaded.zip")
EXTRACT_PATH = os.path.join(TEMP_DIR, "cookiebatch_extracted")

# Default Install Directory - use Documents folder instead of home directory
DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Documents", "CookieBatch")

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

# Check if we're already trying to run with admin rights
ADMIN_FLAG = "--running-as-admin"

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin_privileges():
    """Request administrator privileges. Returns True if already admin or successfully elevated."""
    if is_admin():
        return True
        
    try:
        # The current executable path
        script = sys.executable
        
        # Add a flag to indicate we're already trying to run as admin
        # This prevents an infinite loop if elevation fails
        args = " ".join([f'"{arg}"' for arg in sys.argv])
        if ADMIN_FLAG not in args:
            args += f" {ADMIN_FLAG}"
        
        # Request elevation (UAC)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", script, args, None, 1)
        
        # Exit current instance
        sys.exit()
    except Exception as e:
        print(f"Failed to restart with admin privileges: {e}")
        return False

def check_dir_writeable(path):
    """Check if the directory is writeable."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            os.rmdir(path)
            return True
        except Exception:
            return False
    else:
        test_file = os.path.join(path, "write_test.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception:
            return False

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
            # Create directory for the download file if it doesn't exist
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # Check if we have permission to write to the target file
            try:
                with open(self.save_path, 'w') as test_file:
                    test_file.write("test")
            except PermissionError:
                self.error_occurred.emit("Permission denied when writing to download location.")
                return
                
            # Remove test file if it was created
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
                
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

            # Verify the downloaded file
            if not os.path.exists(self.save_path) or os.path.getsize(self.save_path) == 0:
                self.error_occurred.emit("Download failed: File is empty or doesn't exist.")
                return
                
            # Emit download complete signal
            self.download_complete.emit()

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Connection error: Please check your internet connection.")
        except requests.exceptions.HTTPError as e:
            self.error_occurred.emit(f"HTTP error: {str(e)}")
        except PermissionError:
            self.error_occurred.emit("Permission denied when writing files.")
        except Exception as e:
            self.error_occurred.emit(f"Download failed: {str(e)}")

class Installer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(500, 450)  # Slightly smaller since we don't need the admin button
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
        
        main_layout.addSpacing(20)
        
        # Admin status
        admin_status = "Running with Administrator privileges" if is_admin() else "Running without Administrator privileges"
        self.admin_label = QLabel(admin_status)
        self.admin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.admin_label.setStyleSheet(f"color: {'#4CAF50' if is_admin() else '#F44336'};")
        main_layout.addWidget(self.admin_label)
        
        main_layout.addSpacing(10)
        
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
        
        # Check permission for the selected path
        self.permission_label = QLabel("")
        self.permission_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.permission_label)
        
        # Shortcut creation checkbox
        self.create_shortcut_checkbox = QCheckBox("Create Desktop Shortcut")
        self.create_shortcut_checkbox.setStyleSheet(f"color: {TEXT_COLOR};")
        self.create_shortcut_checkbox.setChecked(True)
        main_layout.addWidget(self.create_shortcut_checkbox)
        
        # Close apps checkbox
        self.close_apps_checkbox = QCheckBox("Close related applications before installation")
        self.close_apps_checkbox.setStyleSheet(f"color: {TEXT_COLOR};")
        self.close_apps_checkbox.setChecked(True)
        main_layout.addWidget(self.close_apps_checkbox)
        
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
        version_label = QLabel("Installer v1.2.0")
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
        self.update_permission_status()
        self.status_label.setText(f"Ready to install to: {self.install_dir}")

    def update_permission_status(self):
        """Update the permission status label."""
        if check_dir_writeable(self.install_dir):
            self.permission_label.setText("✅ Write permission verified for this location")
            self.permission_label.setStyleSheet(f"color: #4CAF50;")
            self.install_button.setEnabled(True)
        else:
            self.permission_label.setText("❌ No write permission for this location")
            self.permission_label.setStyleSheet(f"color: #F44336;")
            # Even with admin, some locations might be restricted
            if is_admin():
                self.permission_label.setText("❌ No write permission even with admin rights")

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
            self.update_permission_status()
            self.status_label.setText(f"Ready to install to: {path}")

    def close_related_applications(self):
        """Attempt to close any applications that might be using target files."""
        if not self.close_apps_checkbox.isChecked():
            return
            
        if platform.system() == "Windows":
            try:
                # Attempt to close any CookieBatch instances using taskkill
                os.system("taskkill /f /im CookieBatch.exe 2>nul")
                # Also try to close any Python instances that might be running it
                os.system("taskkill /f /im python.exe /fi \"WINDOWTITLE eq CookieBatch*\" 2>nul")
                return True
            except Exception:
                pass
        return False

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
                raise ValueError("No Python script or executable found in the installation directory")
        
            # Use winshell to create desktop shortcut on Windows
            desktop = winshell.desktop()
            path = os.path.join(desktop, "CookieBatch.lnk")
        
            # Try to remove existing shortcut if it exists
            if os.path.exists(path):
                try:
                    os.remove(path)
                except PermissionError:
                    # If we can't remove it, just create a new one with a different name
                    path = os.path.join(desktop, "CookieBatch (New).lnk")
        
            # Use python executable to run the script if it's a .py file
            if script_path.endswith('.py'):
                target = sys.executable
                arguments = f'"{script_path}"'
            else:
                target = script_path
                arguments = ""
        
            winshell.CreateShortcut(
                Path=path,
                Target=target,
                Arguments=arguments,
                Icon=(script_path, 0),
                Description="CookieBatch - Python Batch Code Obfuscator",
                StartIn=os.path.dirname(script_path)  # Set working directory to script location
            )
        
            return True
        except PermissionError:
            QMessageBox.warning(self, "Shortcut Creation Warning", 
                            "Permission denied when creating desktop shortcut.")
            return False
        except Exception as e:
            QMessageBox.warning(self, "Shortcut Creation Warning", 
                            f"Could not create desktop shortcut: {e}")
            return False

    def safe_remove(self, path):
        """Safely remove a file or directory with retries."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return True
            except PermissionError:
                # If permission error, wait a bit and retry
                if attempt < max_attempts - 1:
                    self.status_label.setText(f"Retrying file operation...")
                    self.close_related_applications()  # Try to close apps again
                    import time
                    time.sleep(1)  # Wait a second before retry
                else:
                    raise
            except FileNotFoundError:
                # If the file doesn't exist, that's fine
                return True
        return False

    def safe_move(self, src, dest):
        """Safely move files with retries."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # If destination exists, try to remove it first
                if os.path.exists(dest):
                    self.safe_remove(dest)
                
                # Move the file/directory
                shutil.move(src, dest)
                return True
            except PermissionError:
                # If permission error, wait a bit and retry
                if attempt < max_attempts - 1:
                    self.status_label.setText(f"Retrying file operation...")
                    self.close_related_applications()  # Try to close apps again
                    import time
                    time.sleep(1)  # Wait a second before retry
                else:
                    raise
        return False

    def start_installation(self):
        """Start the installation process."""
        # Double-check permissions for the installation directory
        if not check_dir_writeable(self.install_dir):
            QMessageBox.warning(self, "Permission Error", 
                               f"Cannot write to {self.install_dir}. Please select a different location.")
            return
            
        # Close any applications that might be using the files
        self.close_related_applications()
            
        # Disable buttons during installation
        self.install_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Clean up any existing temporary files before starting
        try:
            if os.path.exists(ZIP_PATH):
                self.safe_remove(ZIP_PATH)
            if os.path.exists(EXTRACT_PATH):
                self.safe_remove(EXTRACT_PATH)
        except Exception as e:
            self.on_installation_error(f"Failed to clean up temporary files: {str(e)}")
            return
            
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
                
            # Create extraction directory
            os.makedirs(EXTRACT_PATH, exist_ok=True)

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
            
            self.status_label.setText("Installing files...")

            # Try to close any applications that might be using the files one more time
            self.close_related_applications()

            # Move extracted files
            total_items = len(os.listdir(EXTRACT_PATH))
            for i, item in enumerate(os.listdir(EXTRACT_PATH), 1):
                src = os.path.join(EXTRACT_PATH, item)
                dest = os.path.join(self.install_dir, item)

                try:
                    self.safe_move(src, dest)
                    # Update progress based on file moving
                    self.progress_bar.setValue(int((i / total_items) * 100))
                except PermissionError:
                    raise PermissionError(f"Permission denied when moving {item} to {dest}. Make sure no applications are using these files.")
                    
            self.status_label.setText("Cleaning up...")

            # Clean up temporary files
            try:
                self.safe_remove(ZIP_PATH)
                self.safe_remove(EXTRACT_PATH)
            except Exception as e:
                # Just log this error, don't abort the installation
                print(f"Cleanup warning: {e}")

            # Create desktop shortcut if checkbox is checked
            shortcut_created = False
            if self.create_shortcut_checkbox.isChecked():
                # Only create shortcut on Windows
                if platform.system() == "Windows":
                    self.status_label.setText("Creating desktop shortcut...")
                    shortcut_created = self.create_desktop_shortcut(self.install_dir)

            # Final status update
            self.status_label.setText("Installation completed successfully!")
            self.progress_bar.setValue(100)
            
            # Prepare completion message
            message = f"CookieBatch installed successfully in:\n{self.install_dir}"
            if shortcut_created:
                message += "\n\nDesktop shortcut created."
            
            QMessageBox.information(self, "Installation Complete", message)

        except PermissionError as e:
            self.on_installation_error(f"Permission denied: {str(e)}\nSome files may be locked by other applications.")
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
    # Check if admin flag is present, which means we're already trying to run as admin
    # or we already have admin privileges
    skip_admin_request = ADMIN_FLAG in sys.argv or is_admin()
    
    # Request admin privileges at startup only if needed and not already trying
    if platform.system() == "Windows" and not skip_admin_request:
        request_admin_privileges()
        # The script will exit here if elevation was requested
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern, cross-platform styling
    
    # Set global font to Arial
    app.setFont(QFont("Arial", 10))
    
    window = Installer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()