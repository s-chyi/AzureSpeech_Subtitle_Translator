import os
import json

from time import sleep
from dotenv import load_dotenv
from logs import logger

from datetime import timedelta
from threading import Event
from PySide6 import QtCore

import azure.cognitiveservices.speech as speechsdk
from google.cloud import translate

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "code/google_tccichat_credentials.json"
NAME = "Azure_Dr. George Westerman"
FILE_NAME = "C:\\Project\\AzureSpeech_Subtitle_Translator\\test_data\\Dr. George Westerman.wav"

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