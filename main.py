import sys
import threading
from PyQt5.QtWidgets import QApplication
from src.transparent_window import TransparentWindow, Communicator
from src.continuous_translation import ContinuousTranslation
from dotenv import load_dotenv

load_dotenv()

def start_translation():
    app = QApplication(sys.argv)

    window = TransparentWindow()
    window.show()

    communicator = Communicator()

    translator = ContinuousTranslation(communicator)
    communicator.signal.connect(window.update_text)

    translation_thread = threading.Thread(target=translator.translation_continuous, daemon=True)
    translation_thread.start()

    sys.exit(app.exec_())

if __name__ == "__main__":
    start_translation()