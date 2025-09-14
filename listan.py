
import speech_recognition as sr
from googletrans import Translator, LANGUAGES

translator = Translator()
translator_active = False  # Flag to track if translator is active


def listen():
    global translator_active  # Access the global variable to track translation status
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 34000
    recognizer.dynamic_energy_adjustment_damping = 0.010
    recognizer.dynamic_energy_ratio = 1.0
    recognizer.pause_threshold = 0.8  # Increased to prevent cutting off speech
    recognizer.operation_timeout = None
    recognizer.non_speaking_duration = 0.5  # Slightly increased for better silence detection

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Longer duration for noise adjustment
        while True:
            print("I am Listening...", end="", flush=True)
            try:
                audio = recognizer.listen(source, timeout=None)
                print("\rGot it, Now Recognizing...", end="", flush=True)
                recognized_txt = recognizer.recognize_google(audio).lower()

                # Check if user commands to activate/deactivate translator
                if "activate translator" in recognized_txt:
                    translator_active = True
                    print("Activating the Translator Sir...")
                    print("\rTranslator activated.")
                    continue  # Continue listening after activating

                elif "deactivate" in recognized_txt:
                    translator_active = False
                    print("I am deactivated the Translator Sir...")
                    print("\rTranslator deactivated.")
                    continue  # Continue listening after deactivating

                # If translator is active, detect and translate the language
                if translator_active:
                    # Detect the language of the recognized text
                    detected_lang = translator.detect(recognized_txt).lang
                    
                    # Translate to English if it's not already in English
                    if detected_lang != 'en':
                        translated_text = translator.translate(recognized_txt, dest='en').text
                        print(f"\rMohammod Ibrahim (Detected Language: {LANGUAGES[detected_lang]}): {translated_text}")
                    else:
                        print(f"\rMohammod Ibrahim: {recognized_txt}")
                else:
                    # Just print the recognized text without translation
                    print(f"\rMohammod Ibrahim: {recognized_txt}")
                
                return recognized_txt
            except sr.UnknownValueError:
                print("\rSorry, I didn't catch that. Please try again.", flush=True)
                continue
            except sr.RequestError as e:
                print(f"\rGoogle Speech Recognition service error: {e}")
                return ""
            finally:
                print("\r", end="", flush=True)