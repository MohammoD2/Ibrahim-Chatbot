import os
import sys
import pygame
import edge_tts
import asyncio

def resource_path(relative_path):
    """Get the absolute path to the resource (works for dev and PyInstaller)."""
    try:
        base_path = sys._MEIPASS  # For PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def speak(text, voice='en-US-EricNeural', file_name="data.mp3"):
    """
    Converts text to speech using edge-tts and plays it using pygame.
    This function encapsulates asynchronous calls internally.
    """
    async def async_speak():
        try:
            # Initialize the TTS client and generate the speech file asynchronously.
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(file_name)
            
            # Resolve the absolute path of the file.
            file_path = resource_path(file_name)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file '{file_path}' not found.")
            
            # Initialize pygame and its mixer.
            pygame.init()
            pygame.mixer.init()
            
            # Load and play the audio.
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait until the audio finishes playing.
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            # Only stop/quit the mixer if it was successfully initialized.
            if pygame.mixer.get_init():
                try:
                    pygame.mixer.music.stop()
                except Exception as ex:
                    print(f"Error stopping music: {ex}")
                pygame.mixer.quit()

    # Run the asynchronous speak function inside this synchronous function.
    asyncio.run(async_speak())

# Example usage
if __name__ == "__main__":
    text = "Hello, this is a test of the text-to-speech system."
    speak(text)