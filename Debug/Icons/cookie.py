import random
import string
import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QHBoxLayout, QProgressBar, QDialog
)
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QPixmap, QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QTimer, QSize

# Create a global variable to hold a reference to the main window
main_application_window = None

app = QApplication(sys.argv)

# Load global font with better error handling
font_family = "Arial"  # Default font as fallback
try:
    font_path = "Fonts\\JetBrainsMono-Bold.ttf"
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    font = QFont(font_family, 12)
    app.setFont(font)
    print(f"Main font loaded: {font_family}")
except Exception as e:
    print(f"Error loading main font: {e}")
    font = QFont("Arial", 12)
    app.setFont(font)

# Load input/output font with better error handling
input_output_font_family = "Arial"  # Default font as fallback
try:
    input_output_font_path = "Fonts\\JetBrainsMono-Medium.ttf"
    input_output_font_id = QFontDatabase.addApplicationFont(input_output_font_path)
    if input_output_font_id != -1:
        input_output_font_family = QFontDatabase.applicationFontFamilies(input_output_font_id)[0]
    input_output_font = QFont(input_output_font_family, 10)
    print(f"Input/output font loaded: {input_output_font_family}")
except Exception as e:
    print(f"Error loading input/output font: {e}")
    input_output_font = QFont("Arial", 10)

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

# Define common styling
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
"""

INPUT_STYLE = f"""
    QLineEdit {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 3px;
        padding: 8px;
        background-color: {SECONDARY_BG_COLOR};
        color: {TEXT_COLOR};
    }}
    QLineEdit:focus {{
        border: 1px solid {ACCENT_COLOR};
    }}
"""

TEXT_AREA_STYLE = f"""
    QTextEdit {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 3px;
        padding: 8px;
        background-color: {SECONDARY_BG_COLOR};
        color: {TEXT_COLOR};
    }}
"""

PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 5px;
        text-align: center;
        background-color: {SECONDARY_BG_COLOR};
        color: {TEXT_COLOR};
    }}
    QProgressBar::chunk {{
        background-color: {PRIMARY_COLOR};
        border-radius: 5px;
    }}
"""

def generateGOT():
    accepted_characters = string.ascii_letters + string.digits
    return ''.join(random.choice(accepted_characters) for _ in range(16))

class StartScreen(QWidget):
    def __init__(self):
        super().__init__()
        print("Initializing StartScreen")
        self.setWindowTitle("CookieBatch")
        try:
            self.setWindowIcon(QIcon("Icons\\favicon.ico"))
            print("StartScreen icon loaded")
        except Exception as e:
            print(f"Could not load StartScreen icon: {e}")
        self.setupUI()
        
    def setupUI(self):
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with larger font
        title_font = QFont(font_family, 24, QFont.Weight.Bold)
        title_label = QLabel("CookieBatch")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {ACCENT_COLOR};")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_font = QFont(font_family, 12)
        subtitle_label = QLabel("Batch Code Obfuscator")
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(subtitle_label)
        
        # Add some space
        layout.addSpacing(30)
        
        # Cookie icon or placeholder
        try:
            cookie_pixmap = QPixmap("Icons\\cookie.png")
            cookie_label = QLabel()
            cookie_label.setPixmap(cookie_pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
            cookie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(cookie_label)
            print("Cookie icon loaded")
        except Exception as e:
            print(f"Could not load cookie icon: {e}")
            # Fallback if no icon is available
            cookie_text = QLabel("🍪")
            cookie_text.setFont(QFont(font_family, 32))
            cookie_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(cookie_text)
        
        layout.addSpacing(30)
        
        # Start button
        self.start_button = QPushButton("Start Obfuscator")
        self.start_button.setFont(QFont(font_family, 14))
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet(BUTTON_STYLE)
        layout.addWidget(self.start_button)
        
        # Version info
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet(f"color: {DARKER_TEXT_COLOR};")
        layout.addWidget(version_label)
        
        self.setLayout(layout)
        print("StartScreen UI setup complete")

    def closeEvent(self, event):
        print("StartScreen closing")
        event.accept()

class ObfuscatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        print("Initializing ObfuscatorGUI")
        self.setWindowTitle("CookieBatch")
        try:
            self.setWindowIcon(QIcon("Icons\\favicon.ico"))
            print("ObfuscatorGUI icon loaded")
        except Exception as e:
            print(f"Could not load ObfuscatorGUI icon: {e}")
        self.setupUI()
        self.animation = None  # Store animation reference
        self.original_positions = {}  # Store original positions of widgets
        print("ObfuscatorGUI initialization complete")

    def setupUI(self):
        # Apply the same background color
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Title to match start screen
        title_font = QFont(font_family, 18, QFont.Weight.Bold)
        title_label = QLabel("CookieBatch")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {ACCENT_COLOR};")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_font = QFont(font_family, 10)
        subtitle_label = QLabel("Batch Code Obfuscator")
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(15)

        # Input for the code to obfuscate
        self.code_label = QLabel("Enter BATCH code to obfuscate:")
        self.code_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self.code_label)
        self.code_input = QLineEdit()
        self.code_input.setFont(input_output_font)
        self.code_input.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.code_input)

        # Input for the divide method
        self.divide_label = QLabel("Enter a divide method:")
        self.divide_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self.divide_label)
        self.divide_input = QLineEdit()
        self.divide_input.setFont(input_output_font)
        self.divide_input.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.divide_input)

        # Button to trigger obfuscation
        self.obfuscate_button = QPushButton("Obfuscate")
        self.obfuscate_button.setFont(QFont(font_family, 12))
        self.obfuscate_button.setMinimumHeight(40)
        self.obfuscate_button.setStyleSheet(BUTTON_STYLE)
        self.obfuscate_button.clicked.connect(self.cookie_obfuscate)
        layout.addWidget(self.obfuscate_button)

        # Output text area
        output_label = QLabel("Obfuscated Output:")
        output_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(output_label)
        
        self.output_area = QTextEdit()
        self.output_area.setFont(input_output_font)
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet(TEXT_AREA_STYLE)
        layout.addWidget(self.output_area)

        self.setLayout(layout)
        self.setFixedSize(400, 500)  # Slightly larger to accommodate the title and spacing
        print("ObfuscatorGUI UI setup complete")

    def closeEvent(self, event):
        print("ObfuscatorGUI window closing")
        event.accept()  # allow the window to be closed

    def set_input_error(self, widget, is_error):
        """Sets a red outline on an input field if there's an error, and shakes the widget."""
        if is_error:
            widget.setStyleSheet(f"border: 2px solid #e74c3c; border-radius: 3px; padding: 8px; background-color: {SECONDARY_BG_COLOR}; color: {TEXT_COLOR};")
            self.shake_widget(widget)  # Shake effect on error
        else:
            widget.setStyleSheet(INPUT_STYLE)  # Reset to standard style when corrected

    def shake_widget(self, widget):
        """Animates the widget to shake left and right quickly and return to original position."""
        try:
            # Store the original position if we don't have it yet
            widget_id = id(widget)
            if widget_id not in self.original_positions:
                self.original_positions[widget_id] = widget.pos()
            
            original_pos = self.original_positions[widget_id]
            
            # If there's already an animation running, stop it and reset position
            if self.animation is not None and self.animation.state() == 2:  # 2 is Running state
                self.animation.stop()
                widget.move(original_pos)
                return
            
            # Create a new animation
            self.animation = QPropertyAnimation(widget, b"pos")
            self.animation.setDuration(300)  # 300ms total animation
            self.animation.setStartValue(original_pos)
            
            # Add keyframes for the shake effect
            self.animation.setKeyValueAt(0.1, original_pos + QPoint(-5, 0))  # Left
            self.animation.setKeyValueAt(0.2, original_pos + QPoint(5, 0))   # Right
            self.animation.setKeyValueAt(0.3, original_pos + QPoint(-5, 0))  # Left
            self.animation.setKeyValueAt(0.4, original_pos + QPoint(5, 0))   # Right
            self.animation.setKeyValueAt(0.5, original_pos + QPoint(-3, 0))  # Small left
            self.animation.setKeyValueAt(0.6, original_pos + QPoint(3, 0))   # Small right
            self.animation.setKeyValueAt(0.7, original_pos + QPoint(-2, 0))  # Smaller left
            self.animation.setKeyValueAt(0.8, original_pos + QPoint(2, 0))   # Smaller right
            
            # Make sure it ends at the original position
            self.animation.setEndValue(original_pos)
            
            # Connect the finished signal to ensure widget returns to original position
            self.animation.finished.connect(lambda: self.reset_widget_position(widget, original_pos))
            
            self.animation.start()
        except Exception as e:
            print(f"Error in shake_widget: {e}")

    def reset_widget_position(self, widget, original_pos):
        """Ensure widget returns to its original position after animation"""
        try:
            widget.move(original_pos)
        except Exception as e:
            print(f"Error in reset_widget_position: {e}")

    def cookie_obfuscate(self):
        try:
            print("Starting obfuscation process")
            unobfuscated_code = self.code_input.text().strip()
            divide_text = self.divide_input.text().strip()

            try:
                divide_method = int(divide_text)
            except ValueError:
                print("Invalid divide method: not a number")
                self.set_input_error(self.divide_input, True)
                return

            # Validate input
            is_code_valid = len(unobfuscated_code) > 0
            is_divide_valid = divide_method > 0

            self.set_input_error(self.code_input, not is_code_valid)
            self.set_input_error(self.divide_input, not is_divide_valid)

            if not (is_code_valid and is_divide_valid):
                print("Invalid inputs")
                return  # Stop if inputs are invalid

            # Remove red border when inputs are corrected
            self.set_input_error(self.code_input, False)
            self.set_input_error(self.divide_input, False)

            # Adjust divide_method if it's larger than the code length
            code_length = len(unobfuscated_code)
            divide_method = min(divide_method, code_length)

            code_number_remainder = code_length % divide_method
            code_number = code_length // divide_method
            calcs_needed = code_number if code_number_remainder == 0 else code_number + 1

            tokens_available = [generateGOT() + str(i + 1) for i in range(calcs_needed)]
            split_code = [unobfuscated_code[i * divide_method:(i + 1) * divide_method] for i in range(calcs_needed)]

            unscrambled_code = [f"SET {tokens_available[i]} = {split_code[i]}" for i in range(calcs_needed)]
            concatenated_cmd = "&" + "&&".join(tokens_available) + "&"

            output_text = "\n".join(unscrambled_code) + "\n" + concatenated_cmd
            self.output_area.setPlainText(output_text)
            print("Obfuscation completed successfully")
        except Exception as e:
            print(f"Error in cookie_obfuscate: {e}")
            import traceback
            traceback.print_exc()

# Simple modal loading dialog instead of splash screen
class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Initializing LoadingDialog")
        self.setWindowTitle("Loading")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setFixedSize(400, 150)
        self.completed = False
        
        # Set background color to match other screens
        self.setStyleSheet(f"background-color: {BACKGROUND_COLOR};")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Loading label
        self.loading_label = QLabel("Loading CookieBatch...")
        self.loading_label.setFont(QFont(font_family, 14))
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet(f"color: {ACCENT_COLOR};")
        layout.addWidget(self.loading_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Timer for fake loading progress
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        print("LoadingDialog initialization complete")
        
    def start_loading(self):
        print("Loading started")
        self.timer.start(50)  # Update every 50ms
        
    def update_progress(self):
        self.progress_value += 5
        self.progress_bar.setValue(self.progress_value)
        
        # Update loading message based on progress
        if self.progress_value < 30:
            self.loading_label.setText("Loading resources...")
        elif self.progress_value < 60:
            self.loading_label.setText("Initializing components...")
        elif self.progress_value < 90:
            self.loading_label.setText("Preparing application...")
        else:
            self.loading_label.setText("Almost ready...")
            
        # When complete, stop the timer and mark as completed
        if self.progress_value >= 100:
            print("Loading complete, progress at 100%")
            self.timer.stop()
            self.completed = True
            self.accept()  # This will close the dialog and return exec_() = QDialog.Accepted

def show_main_application():
    global main_application_window  # Reference the global variable
    print("Starting show_main_application()")
    start_screen = StartScreen()
    
    # Function to handle the start button click
    def on_start_clicked():
        global main_application_window  # Reference the global variable again
        print("Start button clicked")
        start_screen.hide()  # Hide instead of close in case we need to show it again
        
        # Create loading dialog
        loading_dialog = LoadingDialog(start_screen)  # Set parent
        
        # Start loading and show the dialog
        loading_dialog.start_loading()
        print("Showing loading dialog")
        result = loading_dialog.exec()  # This will block until the dialog is closed
        print(f"Loading dialog closed with result: {result}")
        
        # If loading completed successfully
        if result == QDialog.DialogCode.Accepted and loading_dialog.completed:
            print("Creating ObfuscatorGUI")
            main_application_window = ObfuscatorGUI()
            main_application_window.show()
            print("ObfuscatorGUI shown")
        else:
            # If loading was cancelled or failed, show the start screen again
            print("Loading canceled or failed, showing start screen again")
            start_screen.show()
    
    # Connect button click
    start_screen.start_button.clicked.connect(on_start_clicked)
    start_screen.show()
    print("Start screen shown")

if __name__ == "__main__":
    try:
        print("Starting application...")
        show_main_application()
        print("Main application window created, starting event loop...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        # Keep console window open on error to see what went wrong
        input("Press Enter to exit...")