from groq import Groq
import argostranslate.package
import speech_recognition as sr
import queue
from io import BytesIO
import io
import threading
import time
import argostranslate.translate
from gtts import gTTS
import pygame

from_code = "es"
to_code = "en"

# Download and install Argos Translate package
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    )
)
argostranslate.package.install_from_path(package_to_install.download())

# Initialize the mixer module
pygame.mixer.init()

#speech
language = to_code

recognizer = sr.Recognizer()

# Queue for audio data
audio_queue = queue.Queue()

speech_thread = None
speech_stop_event = threading.Event()

client = Groq(api_key="API_KEY")

def translate(text):
    # Translate
    translatedText = argostranslate.translate.translate(text, from_code, to_code)
    
    return translatedText
    # '¡Hola Mundo!'
    
running = True

def audio_listener():
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... Press Ctrl+C to stop.")
        
        while running:
            try:
                # Adjusting listen parameters for faster response
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                audio_queue.put(audio)
            except sr.WaitTimeoutError:
                continue
            except KeyboardInterrupt:
                print("Stopping audio listener.")
                break
            except Exception as e:
                print(f"Error in audio listener: {e}")

def audio_processor():
    while running:
        try:
            audio = audio_queue.get()
            print("Transcribing...")
            # Use in-memory stream to avoid file I/O
            audio_data = BytesIO(audio.get_wav_data())
            transcription = client.audio.transcriptions.create(
                file=("temp_audio.wav", audio_data),
                model="whisper-large-v3",
                language=from_code,
                response_format="verbose_json",
            )
            text = transcription.text.strip()
            print(f"Recognized Text: '{text}'")
            if text:
                if text != 'Gracias.':
                    say(translate(text))
            else:
                print("No meaningful speech detected.")
        except Exception as e:
            print(f"Error in audio processor: {e}")


def say(text):
    # Creating a gTTS object and save audio to memory
    speech = gTTS(text=text, lang=language, slow=False)
    audio_fp = io.BytesIO()  # Use an in-memory file
    speech.write_to_fp(audio_fp)
    audio_fp.seek(0)  # Reset pointer to the beginning of the file
        
    # Load the audio into pygame
    pygame.mixer.music.load(audio_fp, 'mp3')  # Load directly from memory
    pygame.mixer.music.play()
        
    # Play the audio and stop if the stop event is set
    while pygame.mixer.music.get_busy():
        if speech_stop_event.is_set():
            pygame.mixer.music.stop()  # Stop the audio playback
            break
        time.sleep(0.1)

# Run the listener and processor in separate threads
listener_thread = threading.Thread(target=audio_listener)
processor_thread = threading.Thread(target=audio_processor)

listener_thread.start()
processor_thread.start()

# Ensure threads continue running until a stop signal
try:
    while running:
        time.sleep(1)  # Main thread does nothing, just keeps the script running
except KeyboardInterrupt:
    print("Stopping script.")
    running = False

# Wait for threads to finish
listener_thread.join()
processor_thread.join()
