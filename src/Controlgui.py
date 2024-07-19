from PySide6 import QtWidgets

class ControlWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Controls")
        self.setGeometry(200, 200, 400, 100)
        
        self.button_layout = QtWidgets.QHBoxLayout(self)
        
        self.start_button = self.create_button("Start Recognition", "green")
        self.pause_button = self.create_button("Pause Recognition", "red", True)
        self.clear_button = self.create_button("Clear History", "blue")
        self.window_button = self.create_button("New Window", "orange")
        
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.pause_button)
        self.button_layout.addWidget(self.clear_button)
        self.button_layout.addWidget(self.window_button)

    def create_button(self, text, color, is_disabled=False):
        button = QtWidgets.QPushButton(text)
        button.setStyleSheet(self.button_stylesheet(color))
        button.setDisabled(is_disabled)
        return button

    @staticmethod
    def button_stylesheet(color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }}
            QPushButton:disabled {{
                background-color: grey;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }}
        """
