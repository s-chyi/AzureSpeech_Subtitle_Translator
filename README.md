# Azure Speech Subtitle Translator Project
## Table of Contents
- Project Overview
- Installation
- Usage
- Files and Directories
- Features

## Project Overview
Azure Speech Subtitle Translator is a project that leverages Azure Cognitive Services and the Google Cloud Translation API to provide real-time speech recognition and subtitle translation. The project translates speech from English to Chinese and vice versa, displaying the subtitles in a sleek GUI.

## Installation
This project requires Python 3.11 or higher. Follow the steps below to setup the project environment:

1. Clone the repository:

```sh
git clone https://github.com/<your_repo>/AzureSpeech_Subtitle_Translator.git
cd AzureSpeech_Subtitle_Translator
```
2. Create a virtual environment:
```sh
conda create -n translator python==3.11
conda activate translator
```
3. Install required packages:

```sh
pip install -r requirements.txt
```
4. Setup environment variables:
    - Create a .env file in the project root directory and add the following:
    ```makefile
    SPEECH_KEY=<Your Azure Speech API Key>
    SPEECH_REGION=<Your Azure Speech API Region>
    GOOGLE_APPLICATION_CREDENTIALS=code/google_tccichat_credentials.json
    ```
## Usage
To run the application, execute the following command:

```sh
python main.py
```

## Files and Directories
- main.py: The main entry point of the application.
- src/: The functioal apps.
- logs/: Contains logging configurations and files.
- output/: Directory where output logs and translations are stored.
- code/: Directory containing images and credentials required for the project.

## Features
1. **Real-time Speech Recognition**: Uses Azure Cognitive Services to recognize speech in real-time.
2. **Translation**: Translates recognized speech between English and Chinese using Google Cloud Translation API.
3. **GUI**: Displays subtitles in real-time in a user-friendly interface.
4. **Control Panel**: A separate control window to manage recognition process.