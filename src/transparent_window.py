from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

class Communicator(QObject):
    signal = pyqtSignal(str)

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)
        screen = self.adjustSizeAndPosition()
        self.setupLabel(screen)

    def adjustSizeAndPosition(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, screen.height() - 200, screen.width(), 200)
        return screen
        
    def setupLabel(self, screen):
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 128);")
        self.label.setFont(QFont("標楷體", 18))
        self.label.setGeometry(0, 0, screen.width(), 200)

    def update_text(self, text):
        self.label.setText(text)