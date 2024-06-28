# 即時語音翻譯專案

## 簡介

即時語音翻譯專案是一個基於Azure語音服務和PyQt5的語音翻譯應用，能夠將語音翻譯為字幕並顯示在透明窗口上。該應用支持英語語音轉換為繁體中文的實時字幕顯示。

## 文件說明

- `main.py`: 主程序入口，負責初始化應用並啟動翻譯。
- `transparent_window.py`: 定義了 `TransparentWindow` 類，負責顯示透明窗口， `Communicator` 類，負責信號的通信。
- `continuous_translation.py`: 主要邏輯文件，負責語音翻譯和顯示的具體實現。
- `call_llm.py`: 包含調用Azure OpenAI API的函數，用於生成總結內容。