import pyaudio
import torch
import speech_recognition as sr
import threading
import time
import collections
from queue import Queue
import io
import os
import numpy as np

# --- Import your custom speak function ---
from Speak import speak

# --- Import your custom chatbot function ---
from Chatbot import chatbot

# Audio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_SIZE = 512

# Turn-taking and memory
SILENCE_DURATION = 1.5
MEMORY_EXPIRY_SECONDS = 3600
conversation_memory = []

# Load Silero VAD model
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
try:
    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                  model='silero_vad',
                                  force_reload=False)
except Exception as e:
    print(f"Failed to load from torch hub: {e}. Attempting local load.")
    model, utils = torch.hub.load(repo_or_dir='path/to/local/repo',
                                  model='silero_vad',
                                  force_reload=False)

(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
model.to(device)


# --- 1. Memory with Auto-Expiry ---
class AutoExpiringMemory:
    def __init__(self, expiry_seconds):
        self.memory = collections.OrderedDict()
        self.expiry_seconds = expiry_seconds
        self.lock = threading.Lock()
        self.start_cleanup_thread()

    def start_cleanup_thread(self):
        thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        thread.start()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            self.cleanup()

    def cleanup(self):
        with self.lock:
            now = time.time()
            expired_keys = []
            for key, (value, timestamp) in self.memory.items():
                if now - timestamp > self.expiry_seconds:
                    expired_keys.append(key)
                else:
                    break
            for key in expired_keys:
                del self.memory[key]

    def add_message(self, role, text):
        with self.lock:
            key = len(self.memory)
            self.memory[key] = ({"role": role, "parts": [{"text": text}]}, time.time())
            global conversation_memory
            conversation_memory.append({"role": role, "parts": [{"text": text}]})
            if len(conversation_memory) > len(self.memory):
                conversation_memory.pop(0)

    def get_history(self):
        with self.lock:
            return [item[0] for item in self.memory.values()]

memory = AutoExpiringMemory(expiry_seconds=MEMORY_EXPIRY_SECONDS)


# --- 2. Silero VAD and Turn-Taking ---
def listen_for_input(audio_queue):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK_SIZE)

    print("Listening...")

    vad_iterator = VADIterator(model, sampling_rate=RATE, min_silence_duration_ms=int(SILENCE_DURATION * 1000))
    frames = []

    while True:
        try:
            audio_chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).copy()
            audio_int16 = torch.from_numpy(audio_np).to(device)

            speech_dict = vad_iterator(audio_int16, return_seconds=True)

            if speech_dict:
                if 'start' in speech_dict:
                    print("Speech detected! Start recording...")
                    frames.append(audio_chunk)
                elif 'end' in speech_dict:
                    print("Silence detected. End of turn.")
                    audio_queue.put(b''.join(frames))
                    frames = []
            elif frames:
                frames.append(audio_chunk)

        except KeyboardInterrupt:
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()


# --- 3. Speech-to-Text and Chatbot Processing ---
def process_conversation(audio_queue, response_queue):
    r = sr.Recognizer()

    while True:
        audio_data_raw = audio_queue.get()
        if not audio_data_raw:
            continue

        try:
            audio_data = sr.AudioData(audio_data_raw, RATE, 2)
            user_text = r.recognize_google(audio_data)
            print(f"You said: {user_text}")

            memory.add_message("user", user_text)

            # Use your custom chatbot function instead of Gemini
            ai_response_text = chatbot(user_text, product="Ibrahim")
            print(f"Chatbot says: {ai_response_text}")

            memory.add_message("model", ai_response_text)
            response_queue.put(ai_response_text)

        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from STT service; {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


# --- 4. Text-to-Speech Output (using your speak function) ---
def play_response(response_queue):
    while True:
        text_to_speak = response_queue.get()
        if not text_to_speak:
            continue
        
        try:
            # --- Use your custom speak function here ---
            print("Playing audio response...")
            speak(text_to_speak)
            # -------------------------------------------
            
        except Exception as e:
            print(f"TTS error: {e}")

# --- Main execution ---
if __name__ == "__main__":
    audio_queue = Queue()
    response_queue = Queue()

    listen_thread = threading.Thread(target=listen_for_input, args=(audio_queue,))
    process_thread = threading.Thread(target=process_conversation, args=(audio_queue, response_queue))
    play_thread = threading.Thread(target=play_response, args=(response_queue,))
    
    listen_thread.daemon = True
    process_thread.daemon = True
    play_thread.daemon = True
    
    listen_thread.start()
    process_thread.start()
    play_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")