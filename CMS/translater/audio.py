"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import os
if "CMS_ACTIVE" in os.environ:
    from . import translator
import speech_recognition as sr

def audio_to_english(audio_path):
    """Convert given Audio File to English

    Args:
        audio_path (str): audio file, path

    Returns:
        text (str): text in english
    """
    # Step 1: Convert audio to text (speech-to-text)
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)  # Uses Google Web Speech API
        except sr.UnknownValueError:
            return "Audio not understood"
        except sr.RequestError:
            return "API request failed"

    # Step 2: Translate text to English
    translated = translator.translate(text, dest='en')
    return translated.text