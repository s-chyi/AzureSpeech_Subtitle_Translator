import sys
from PySide6 import QtWidgets

from src.Translationgui import TranslationGUI

def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = TranslationGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()