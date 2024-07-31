from PIL.ImageQt import ImageQt
from PIL import Image, ImageEnhance
from PySide6 import QtWidgets, QtGui, QtCore

IMAGE_PATH = "code/AI 07a_00001.jpg" #AI 07a_00000.jpg #AI 07a_00001.jpg #background_new_AI.jpg
ZH_FONT_SIZE = [48, 24] 
EN_FONT_SIZE = [48, 28]

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
