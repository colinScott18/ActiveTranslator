from groq import Groq
import speech_recognition as sr
import queue
from io import BytesIO
import threading
import time
import argostranslate.translate
from gtts import gTTS
import pygame

from_code = "en"
to_code = "es"

pygame.mixer.init()

#speech
language = 'es'

recognizer = sr.Recognizer()

# Queue for audio data
audio_queue = queue.Queue()

speech_thread = None
speech_stop_event = threading.Event()

client = Groq(api_key="key")

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
                language="en",
                response_format="verbose_json",
            )
            text = transcription.text.strip()
            print(f"Recognized Text: '{text}'")
            if text:
                if text != 'Thank you.':
                    say(translate(text))
            else:
                print("No meaningful speech detected.")
        except Exception as e:
            print(f"Error in audio processor: {e}")

def say(text):
    myobj = gTTS(text=text, lang=language, slow=False)

    # Saving the converted audio in a mp3 file named
    # welcome 
    myobj.save("es.mp3")

    # Load the mp3 file
    pygame.mixer.music.load("es.mp3")

    # Play the loaded mp3 file
    pygame.mixer.music.play()

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
