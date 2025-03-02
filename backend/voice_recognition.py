from backend.general import config, end_safely

import os
import sys
import re
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError


def convert_sound_file(filename: str) -> str:
    pattern = r"([^\\/]+)\.([^\\/]+)$"
    matches = re.search(pattern, filename)
    converted_name = ""
    if not matches:  # Regex not matching a file with file extension
        print("Faulty file path, does this lead to a file with a valid name and file extension?")
        sys.exit(1)
    if matches[2].lower() in ["wav", "aiff", "aif", "aifc", "flac"]:  # No need to convert when already readable
        return filename
    else:
        if not os.path.exists("conversions"):  # Creates conversions folder if not there
            os.makedirs("conversions")
        try:  # Tries to convert with FFMPEG and file extension
            converted_name = f"conversions/conv_{matches[1]}.wav"
            audio_segment = AudioSegment.from_file(filename, format=matches[2])
            audio_segment.export(converted_name, format="wav")
        except CouldntDecodeError:  # If file extension is not convertable by FFMPEG
            print("Could not decode file. Is file an audio file, and is the file type supported by FFMPEG?")
            end_safely(1)
        except RuntimeWarning:
            print("Could not find FFMPEG. Make sure to install it if you wish to use the attempt_conversion option!")
            end_safely(1)
        return converted_name


# Convert audio file into text using speech recognition
def interpret_sound_file(filename: str) -> str:
    attempt_conversion = config.getboolean("VOICE_RECOGNITION", "attempt_conversion")
    try:                # Try to read the audio file as PCM WAV, AIFF/AIFF-C, or Native FLAC
        if attempt_conversion:
            filename = convert_sound_file(filename)
        r = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            return text
    except ValueError as e:
        print("Audio file could not be read as PCM WAV, AIFF/AIFF-C, or Native FLAC; check if file is corrupted or in another format.")
        end_safely(1)    # Exit program if audio file cannot be read