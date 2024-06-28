import threading
import datetime
import os
import time
from PyQt5.QtCore import QObject, QTimer
import azure.cognitiveservices.speech as speechsdk
from src.call_llm import call_aoai

# Configuration constants
NAME = "Dr. George Westerman" #Ben Armstrong or Dr. George Westerman
FILE_NAME = f"C:\\Project\\即時語音翻譯\\test_data\\{NAME}.wav"

class ContinuousTranslation(QObject):
    def __init__(self, communicator):
        super().__init__()
        self.previous_offset = 0
        self.previous_duration = 0
        self.previous_text = ""
        self.previous_translation = ""
        self.previous_completed_text = ""
        self.previous_completed_translation = ""
        self.segment_text = ""
        self.summary_text = ""
        self.communicator = communicator
        self.log_file = "output/" + NAME + "_log.txt"
        self.output_file_text = "output/" + NAME + "_translated_texts.txt"
        self.output_file_translation = "output/" + NAME + "_translated_texts_zh-Hant.txt"
        self.summary_file = "output/" + NAME + "_summaries.txt"
        self.summary_interval = 30 #幾秒總結一次
        self.clear_files_at_start()
        self.init_summary_timer()

    def clear_files_at_start(self):
        with open(self.output_file_text, 'w', encoding='utf-8'), \
             open(self.output_file_translation, 'w', encoding='utf-8'), \
             open(self.summary_file, 'w', encoding='utf-8'):
            pass

    def init_summary_timer(self):
        self.summary_timer = QTimer()
        self.summary_timer.timeout.connect(self.start_summary_thread)
        self.summary_timer.start(self.summary_interval * 1000)

    def format_time(self, seconds):
        delta = datetime.timedelta(seconds=seconds)
        formatted_time = str(delta).split('.')[0]
        return formatted_time[2:] if formatted_time.startswith("0:") else formatted_time
    
    def update_text_widget(self, text, translation):
        def split_text(text, max_len):
            split_lines = []
            while len(text) > max_len:
                split_lines.append(text[:max_len])
                text = text[max_len:]
            split_lines.append(text)
            return "\n".join(split_lines[-4:])
        
        display_text = split_text((text + translation).replace("\n", ""), 30)
        self.communicator.signal.emit(display_text)

    def translation_continuous(self):
        speech_translation_config = self.create_translation_config()
        audio_config = speechsdk.audio.AudioConfig(filename=FILE_NAME)
        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=speech_translation_config,
            audio_config=audio_config
        )

        done = threading.Event()
        recognizer.session_started.connect(lambda evt: print(f'SESSION STARTED: {evt}'))
        recognizer.session_stopped.connect(lambda evt: self.stop_recognition(evt, done))
        recognizer.canceled.connect(lambda evt: self.stop_recognition(evt, done))
        recognizer.recognizing.connect(self.result_callback)
        recognizer.recognized.connect(self.result_callback)
        recognizer.recognized.connect(self.recognized_callback)

        recognizer.start_continuous_recognition()
        self.wait_for_recognition_to_complete(done)
        recognizer.stop_continuous_recognition()
        self.summary_timer.stop()

    def create_translation_config(self):
        config = speechsdk.translation.SpeechTranslationConfig(
            subscription=os.getenv('SPEECH_KEY'), region=os.getenv('SPEECH_REGION')
        )
        config.speech_recognition_language = "en-US"
        config.add_target_language("zh-Hant")
        config.set_property(speechsdk.PropertyId.Speech_LogFilename, self.log_file)
        config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "300")
        return config

    def stop_recognition(self, evt, done_event):
        print(f'SESSION STOPPED: {evt}')
        done_event.set()

    def wait_for_recognition_to_complete(self, done_event):
        while not done_event.is_set():
            time.sleep(0.1)

    def result_callback(self, evt: speechsdk.translation.TranslationRecognitionEventArgs):
        self.update_text_widget(self.previous_completed_translation, evt.result.translations['zh-Hant'])
        self.previous_text = evt.result.text
        self.previous_translation = evt.result.translations['zh-Hant']
        self.previous_offset = evt.result.offset
        self.previous_duration = evt.result.duration

    def recognized_callback(self, evt: speechsdk.translation.TranslationRecognitionEventArgs):
        start_time = evt.result.offset / 10**7
        end_time = (evt.result.offset + evt.result.duration) / 10**7
        content_text = evt.result.text
        content_translation = evt.result.translations['zh-Hant']

        with open(self.output_file_text, 'a', encoding='utf-8') as f:
            f.write(f"{self.format_time(start_time)}-{self.format_time(end_time)} {content_text}\n")
        
        with open(self.output_file_translation, 'a', encoding='utf-8') as f_zh:
            f_zh.write(f"{self.format_time(start_time)}-{self.format_time(end_time)} {content_translation}\n")

        self.previous_completed_text = content_text
        self.previous_completed_translation = content_translation
        self.segment_text += f"{content_text} "

    def start_summary_thread(self):
        summary_thread = threading.Thread(target=self.perform_summary, daemon=True)
        summary_thread.start()
    
    def perform_summary(self):
        segment_text = self.segment_text[-60000:]
        if self.summary_text:
            prompt = f"演講者為:{NAME}\n\n#####目標:\n\n請總結以下內容：\n\n{segment_text}\n\n#####下列為先前總結內容，請根據整體內容進行總結，請接續總結內容\n\n{self.summary_text}\n\n#####本次總結內容:\n"
        else:
            prompt = f"演講者為:{NAME}\n\n#####目標:\n\n請總結以下內容：\n\n{segment_text}\n\n#####本次總結內容:\n"
        
        response = call_aoai(prompt)
        print(response)
        if response != "無":
            self.summary_text += f"\n{response}"
            
            with open(self.summary_file, 'a', encoding='utf-8') as f_sum:
                f_sum.write(f"Summary at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n")
                f_sum.write(response + "\n")