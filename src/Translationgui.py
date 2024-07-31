from src.Basegui import BaseGUI
from src.Translation import ContinuousTranslation
from src.Controlgui import ControlWindow

from PySide6 import QtWidgets, QtGui, QtCore
from threading import Thread, Event
from re import finditer

NAME = "Azure_Dr. George Westerman"
ZH_FONT_SIZE = [48, 24] 
EN_FONT_SIZE = [48, 28]

class CH2ENGUI(BaseGUI):
    def __init__(self):
        super().__init__("CaptionCraft", 1024, 768)
        self.setup_ui()
        self.ZH_FONT_SIZE = ZH_FONT_SIZE[0]
        self.EN_FONT_SIZE = EN_FONT_SIZE[0]

    def setup_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area_top, 1)
        self.scroll_area_bottom.setVisible(False) 

    def format_text(self, ch_text: str, en_text: str, ch_prev_text: str, en_prev_text: str, full_ch:str, full_en: str):
        formatted_ch_text = full_ch + "<br>" + ch_text if full_ch else ch_text
        formatted_en_text = full_en + "<br>" + en_text if full_en else en_text
        return formatted_ch_text, formatted_en_text

    def update_text(self, ch_text: str, en_text: str, ch_prev_text: str, en_prev_text: str, full_ch:str, full_en: str, is_pause: bool):
        if is_pause:
            return
        formatted_ch_text, formatted_en_text = self.format_text(ch_text, en_text, ch_prev_text, en_prev_text, full_ch, full_en)
        self.type_string(formatted_ch_text, formatted_en_text)

class TranslationGUI(BaseGUI):
    updateTextSignal = QtCore.Signal(str, str, str, str, str, str, bool)

    def __init__(self):
        super().__init__("CaptionCraft", 1024, 768)
        self.translation = ContinuousTranslation(self.updateTextSignal)
        Thread(target=self.translation.translation_continuous, daemon=True).start()
        self.ZH_FONT_SIZE = ZH_FONT_SIZE[0]
        self.EN_FONT_SIZE = EN_FONT_SIZE[0]
        self.ch2en_window = None

        self.control_window = ControlWindow()
        self.control_window.show()

        self.updateTextSignal.connect(self.update_text)
        self.control_window.start_button.clicked.connect(self.start_translation)
        self.control_window.pause_button.clicked.connect(self.pause_translation)
        self.control_window.clear_button.clicked.connect(self.clear_history)
        self.control_window.window_button.clicked.connect(self.create_ch2en_window)

    def create_ch2en_window(self):
        self.ch2en_window = CH2ENGUI()
        self.ch2en_window.show()
        self.updateTextSignal.connect(self.ch2en_window.update_text)
        self.control_window.window_button.setDisabled(False)

    def start_translation(self):
        if self.ch2en_window:
            self.ch2en_window.full_en_text = self.full_en_text 
        self.translation.is_paused.clear()
        self.control_window.start_button.setDisabled(True)
        self.control_window.pause_button.setDisabled(False)

    def pause_translation(self):
        self.translation.is_paused.set()
        self.export_current_text()
        self.control_window.start_button.setDisabled(False)
        self.control_window.pause_button.setDisabled(True)

    def clear_history(self):
        if self.ch2en_window: 
            self.ch2en_window.type_string("", "")

    def export_current_text(self):
        with open(f"output/{NAME}_QA.txt", "a", encoding="utf-8") as text_file:
            text_file.write("Question: \n")
            text_file.write(self.translation.full_ch + "\n" + self.translation.full_en)

    def find_punctuation_index(self, text, forward=True, max_punctuation=3):
        matches = finditer(r"[.!?。！？]", text)
        indexes = [match.start() for match in matches]

        if len(indexes) < max_punctuation:
            return 0
        
        return indexes[max_punctuation-1] + 1 if forward else indexes[-max_punctuation] + 1

    def split_text_at_index(self, text, index):
        return text[:index-1], text[index:]

    def format_text(self, ch_text: str, en_text: str, ch_prev_text: str = "", en_prev_text: str = "") -> tuple:
        while True:
            ch_idx = self.find_punctuation_index(ch_text)
            en_idx = self.find_punctuation_index(en_text)
            if not ch_idx and not en_idx: break
            if ch_idx: ch_prev_text, ch_text = self.split_text_at_index(ch_text, ch_idx)
            if en_idx: en_prev_text, en_text = self.split_text_at_index(en_text, en_idx)

        while True:
            ch_idx = self.find_punctuation_index(ch_prev_text, False, 3)
            en_idx = self.find_punctuation_index(en_prev_text, False, 3)
            if not ch_idx and not en_idx: break
            if ch_idx: _, ch_prev_text = self.split_text_at_index(ch_prev_text, ch_idx) 
            if en_idx: _, en_prev_text = self.split_text_at_index(en_prev_text, en_idx)

        return ch_text, en_text, ch_prev_text, en_prev_text

    def is_synced(self):
        return len(self.translation.full_ch) == len(self.translation.full_en)

    def update_text(self, ch_text: str, en_text: str, ch_prev_text: str, en_prev_text: str, full_ch: str, full_en: str, is_pause: bool):
        ch_text, en_text, ch_prev_text, en_prev_text = self.format_text(ch_text, en_text, ch_prev_text, en_prev_text)
        formatted_ch_text = ch_prev_text + "<br>" + ch_text if full_ch else ch_text
        formatted_en_text = en_prev_text + "<br>" + en_text if full_en else en_text

        if self.translation.is_paused.is_set():
            self.type_string(formatted_ch_text, formatted_en_text)
            if self.is_synced() and self.ch2en_window:
                self.ch2en_window.type_string(formatted_ch_text, formatted_en_text)
        else:
            if self.is_synced() and self.ch2en_window:
                formatted_ch_text, formatted_en_text = self.ch2en_window.format_text(ch_text, en_text, ch_prev_text, en_prev_text, full_ch, full_en)
                self.type_string(formatted_ch_text, formatted_en_text)
                self.ch2en_window.type_string(formatted_ch_text, formatted_en_text)
            else:
                self.type_string(formatted_ch_text, formatted_en_text)