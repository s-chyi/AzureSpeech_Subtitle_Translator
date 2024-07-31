import os
import sys
import json

from time import sleep
from re import finditer
from dotenv import load_dotenv

from logs import logger

from datetime import timedelta
from PIL.ImageQt import ImageQt
from PIL import Image, ImageEnhance
from threading import Thread, Event
from PySide6 import QtWidgets, QtGui, QtCore

import azure.cognitiveservices.speech as speechsdk
# from google.cloud import translate_v2 as translate
from google.cloud import translate


# 加載環境變量
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "code/google_tccichat_credentials.json"

# 常量設置
NAME = "Azure_Dr. George Westerman"
# FILE_NAME = r"C:\Users\andy.wang\Desktop\錄音檔案測試_new\2021-Digital-George-Westerman-Dr. George Westerman.wav"
FILE_NAME = None
IMAGE_PATH = "code/AI 07a_00001.jpg"
ZH_FONT_SIZE = [48, 24] 
EN_FONT_SIZE = [48, 28]


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

class BaseGUI(QtWidgets.QWidget):
    def __init__(self, title, width, height):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)
        self.label = QtWidgets.QLabel(self)
        self.label.setScaledContents(True)
        self.bg_image_original = Image.open(IMAGE_PATH)
        self.bg_image_enhanced = ImageEnhance.Brightness(self.bg_image_original).enhance(1)
        self.scroll_area_top, self.text_area_top = self.create_scroll_area()
        self.scroll_area_bottom, self.text_area_bottom = self.create_scroll_area()

        self.full_ch_text = ""
        self.full_en_text = ""
        self.remaining_ch_text = ""
        self.remaining_en_text = ""
        self.timer = None

        self.ZH_FONT_SIZE = ZH_FONT_SIZE[0]
        self.EN_FONT_SIZE = EN_FONT_SIZE[0]

    def calculate_line_count(self, text, font_size, widget_width):
        font = QtGui.QFont("Times New Roman", font_size)
        font_metrics = QtGui.QFontMetrics(font)
        lines = text.split('<br>')  # 按 <br> 分隔行
        line_count = 0

        for line in lines:
            line_width = font_metrics.horizontalAdvance(line)
            line_count += (line_width // widget_width) + 1  # 計算當行包含的字數

        return line_count
    
    def create_scroll_area(self):
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(self.scroll_area_stylesheet())
        text_area = QtWidgets.QLabel()
        text_area.setWordWrap(True)
        text_area.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft) # AlignJustify
        text_area.setStyleSheet("background-color: rgba(255, 255, 255, 230); padding: 10px;")
        scroll_area.setWidget(text_area)
        scroll_area.viewport().setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        return scroll_area, text_area

    @staticmethod
    def scroll_area_stylesheet():
        return """
            QScrollArea {
                background-color: rgba(255, 255, 255, 0);
                border: none;
            }
            QScrollBar:vertical {
                width: 0;
                background: none;
            }
        """

    def resizeEvent(self, event):
        main_width, main_height = self.width(), self.height()
        resized_bg_image = self.bg_image_enhanced.resize((main_width, main_height))
        self.bg_photo = QtGui.QPixmap.fromImage(ImageQt(resized_bg_image))
        self.label.setPixmap(self.bg_photo)
        self.label.setGeometry(0, 0, main_width, main_height)

        new_width, new_height = int(main_width * 0.95), int(main_height * 0.45)
        x1 = int((main_width - new_width) / 2)
        y1_top = int(main_height * 0.25 - new_height / 2)
        spacing = 20
        y1_bottom = y1_top + new_height + spacing
        self.scroll_area_top.setGeometry(x1, y1_top, new_width, new_height)
        self.scroll_area_bottom.setGeometry(x1, y1_bottom, new_width, new_height)

    def format_display_text(self, ch_text: str, en_text: str) -> tuple:
        formatted_ch_text = f'<p style="font-family: 標楷體; font-size: {self.ZH_FONT_SIZE}px; margin: 0; font-weight: bold;">{ch_text}</p>'
        formatted_en_text = f'<p style="font-family: Times New Roman; font-size: {self.EN_FONT_SIZE}px; margin: 0; font-weight: bold;">{en_text}</p>'
        return formatted_ch_text, formatted_en_text
    
    def type_next_character(self):
        if self.remaining_ch_text or self.remaining_en_text:
            if self.remaining_ch_text:
                self.full_ch_text += self.remaining_ch_text[0]
                self.remaining_ch_text = self.remaining_ch_text[1:]
            if self.remaining_en_text:
                self.full_en_text += self.remaining_en_text[:3]
                self.remaining_en_text = self.remaining_en_text[3:]

            formatted_ch_text, formatted_en_text = self.format_display_text(self.full_ch_text, self.full_en_text)
            self.text_area_top.setText(formatted_en_text)
            self.text_area_bottom.setText(formatted_ch_text)

            QtWidgets.QApplication.processEvents()
            self.scroll_area_top.verticalScrollBar().setValue(self.scroll_area_top.verticalScrollBar().maximum())
            self.scroll_area_bottom.verticalScrollBar().setValue(self.scroll_area_bottom.verticalScrollBar().maximum())
        else:
            self.timer.stop()

    def type_string(self, full_ch_new, full_en_new):
        common_ch_length = min(len(self.full_ch_text), len(full_ch_new))
        common_en_length = min(len(self.full_en_text), len(full_en_new))

        self.full_ch_text = full_ch_new[:common_ch_length]
        self.full_en_text = full_en_new[:common_en_length]

        self.remaining_ch_text = full_ch_new[common_ch_length:]
        self.remaining_en_text = full_en_new[common_en_length:]

        formatted_ch_text, formatted_en_text = self.format_display_text(self.full_ch_text, self.full_en_text)
        self.text_area_top.setText(formatted_en_text)
        self.text_area_bottom.setText(formatted_ch_text)
        QtWidgets.QApplication.processEvents()

        if self.timer:
            self.timer.stop()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.type_next_character)
        self.timer.start()

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

class ContinuousTranslation(QtCore.QObject):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.init_translation_data()
        self.translate_client = translate.TranslationServiceClient()
        self.is_paused = Event()
        self.is_paused.set()

    def init_translation_data(self):
        self.previous_offset = 0
        self.previous_duration = 0
        self.previous_en = ""
        self.previous_ch = ""
        self.previous_completed_en = ""
        self.previous_completed_ch = ""
        self.full_ch = ""
        self.full_en = ""
        self.log_file = f"output/{NAME}_log.txt"
        self.output_file_text = f"output/{NAME}_translated_texts.txt"
        self.output_file_translation = f"output/{NAME}_translated_texts_zh-Hant.txt"
        self.project_id = "tcci-librechat"
        self.glossary_id = "TCC_MIT"

    @staticmethod
    def format_time(seconds: float) -> str:
        delta = timedelta(seconds=seconds)
        formatted_time = str(delta).split('.')[0]
        return formatted_time[2:] if formatted_time.startswith("0:") else formatted_time
    
    def translate_text_with_glossary(
        self,
        client,
        text,
        project_id,
        glossary_id,
        source_lang,
        target_lang
    ) -> translate.TranslateTextResponse:
        """Translates a given text using a glossary.

        Args:
            text: The text to translate.
            project_id: The ID of the GCP project that owns the glossary.
            glossary_id: The ID of the glossary to use.

        Returns:
            The translated text."""
        location = "global"
        parent = f"projects/{project_id}/locations/{location}"

        glossary = client.glossary_path(
            project_id, "global", glossary_id  # The location of the glossary
        )

        glossary_config = translate.TranslateTextGlossaryConfig(glossary=glossary)

        # Supported language codes: https://cloud.google.com/translate/docs/languages
        response = client.translate_text(
            request={
                "contents": [text],
                "target_language_code": target_lang,
                "source_language_code": source_lang,
                "parent": parent,
                "glossary_config": glossary_config,
            }
        )

        return response.glossary_translations[0].translated_text 

    # Initialize Translation client
    def translate_text_zh_en(
        self, client, text: str = "YOUR_TEXT_TO_TRANSLATE", project_id: str = "YOUR_PROJECT_ID"
    ) -> translate.TranslationServiceClient:
        """Translating Text."""

        client = translate.TranslationServiceClient()

        location = "global"

        parent = f"projects/{project_id}/locations/{location}"

        # Translate text from English to French
        # Detail on supported types can be found here:
        # https://cloud.google.com/translate/docs/supported-formats
        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",  # mime types: text/plain, text/html
                "source_language_code": "zh-TW",
                "target_language_code": "en-US",
            }
        )

        return response.translations[0].translated_text 


    def translate_text(self, text, language=None):
        try:
            if language == "en-US":
                return self.translate_text_with_glossary(self.translate_client, text, self.project_id, self.glossary_id, "en-US", "zh-TW"), text
                # return self.translate_client.translate(text, target_language="zh-TW")['translatedText'], text
            else:
                return text, self.translate_text_zh_en(self.translate_client, text, self.project_id)
            # self.translate_text_with_glossary(self.translate_client, text, self.project_id, "TCC_MIT", "zh-TW", "en-US")
        except Exception as e:
            logger.error(f"Error with translate: {e}")
            return ""

    def translation_continuous(self):
        recognizer = self.init_recognizer()
        phrase_list_grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
        self.add_custom_phrases(phrase_list_grammar)
        done = Event()
        self.connect_recognizer_events(recognizer, done)
        recognizer.start_continuous_recognition_async()
        self.wait_for_recognition_to_complete(done)
        recognizer.stop_continuous_recognition_async()

    def init_recognizer(self):
        speech_config = self.create_speech_config()
        audio_config = speechsdk.audio.AudioConfig(filename=FILE_NAME) if FILE_NAME else speechsdk.audio.AudioConfig(use_default_microphone=True)
        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "zh-TW"])
        return speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_source_language_config
        )

    @staticmethod
    def create_speech_config():
        config = speechsdk.SpeechConfig(
            subscription=os.environ.get('SPEECH_KEY'),
            region=os.environ.get('SPEECH_REGION'),
        )
        config.speech_recognition_language = "en-US"
        config.set_property(speechsdk.PropertyId.Speech_LogFilename, "output/speech_log.txt")
        config.enable_dictation()
        config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption, value='TrueText')
        config.set_profanity(speechsdk.ProfanityOption.Raw)
        config.set_property(property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode, value='Continuous')
        return config

    @staticmethod
    def add_custom_phrases(phrase_list_grammar):
        phrases = ["Dr. George Westerman", "Dr. Westerman", "Dr. Ben Armstrong", "Dr. Armstrong",
                   "TCC group", "TCC", "a Senior Lecturer at the MIT Sloan School of Management ",
                   "a Research Scientist of MIT's Industrial Performance Center",
                   "Nelson Chang", "Roman Cheng", "程總", "President Cheng", "台泥集團", "生成式AI", "Generative AI",
                   "Q&A", "舉手按鈕", "Dr.", "博士", "Manufacturing", "製造業", "Digital twin", "數位孿生", "NHOA", "MIT",
                   "CIMPOR", "CIMPOR Global Holdings","麻省理工學院", "Gallery"]
        for phrase in phrases:
            phrase_list_grammar.addPhrase(phrase)

    def connect_recognizer_events(self, recognizer, done):
        recognizer.session_started.connect(lambda evt: print(f'SESSION STARTED: {evt}'))
        recognizer.session_stopped.connect(lambda evt: self.stop_recognition(evt, done))
        recognizer.canceled.connect(lambda evt: self.stop_recognition(evt, done))
        recognizer.recognizing.connect(self.result_callback)
        recognizer.recognized.connect(self.recognized_callback)

    @staticmethod
    def stop_recognition(evt, done_event):
        logger.info(f"Stop recognition by: {evt}")
        print(f'SESSION STOPPED: {evt}')
        done_event.set()

    @staticmethod
    def wait_for_recognition_to_complete(done_event):
        while not done_event.is_set():
            sleep(0.1)

    def result_callback(self, evt: speechsdk.RecognitionEventArgs):
        try:
            if evt.result.reason != speechsdk.ResultReason.NoMatch:
                language = json.loads(evt.result.json)["PrimaryLanguage"]["Language"]
                ch_text, en_text = self.translate_text(evt.result.text, language)
                self.signals.emit(
                    ch_text, en_text, 
                    self.previous_completed_ch, self.previous_completed_en, 
                    self.full_ch, self.full_en,
                    self.is_paused.is_set()
                )
                self.previous_offset, self.previous_duration = evt.result.offset, evt.result.duration
        except Exception as e:
            logger.error(f"Recognized error: {e}")

    def recognized_callback(self, evt: speechsdk.RecognitionEventArgs):
        try:
            if evt.result.reason != speechsdk.ResultReason.NoMatch:
                start_time = evt.result.offset / 10**7
                end_time = (evt.result.offset + evt.result.duration) / 10**7
                text = evt.result.text
                language = json.loads(evt.result.json)["PrimaryLanguage"]["Language"]
                self.previous_completed_ch, self.previous_completed_en = self.translate_text(text, language)
                self.full_ch += self.previous_completed_ch
                self.full_en += self.previous_completed_en
                if len(self.full_ch) > 19*8: self.full_ch = self.full_ch[-19*8:]
                if len(self.full_en) > 60*8: self.full_en = self.full_en[-60*8:]

                self.write_to_file(self.output_file_text, start_time, end_time, self.previous_completed_en)
                self.write_to_file(self.output_file_translation, start_time, end_time, self.previous_completed_ch)
        except Exception as e:
            logger.error(f"Error with: {e}")

    def write_to_file(self, file_path: str, start_time: float, end_time: float, content: str):
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{self.format_time(start_time)}-{self.format_time(end_time)} {content}\n")

def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = TranslationGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
