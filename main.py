import sys
from PyQt6.QtWidgets import QApplication
from views import DigitalBookWindow

def main():
    app = QApplication(sys.argv)
    
    # Set global application properties
    app.setApplicationName("Digital Book")
    
    window = DigitalBookWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()