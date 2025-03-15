import os
import traceback
import pygame
import time
import threading
import queue
import atexit

# Initialize the TTS queue
tts_queue = queue.Queue()

def _tts_worker():
    """Worker thread to process TTS requests from the queue."""
    while True:
        text = tts_queue.get()  # Get the next text from the queue
        if text is None:  # Stop signal
            print("Stopping TTS worker thread.")
            break

        try:
            print(f"Processing text: {text}")
            totts(text)
        except Exception as e:
            print(f"Error during TTS playback: {e}")
        finally:
            tts_queue.task_done()  # Mark task as complete
            print("TTS task done.")


def gotts(text):
    """Add a TTS request to the queue."""
    print(f"Queueing text: {text}")
    tts_queue.put(text)


def stop_tts_worker():
    """Gracefully stop the TTS worker thread."""
    tts_queue.put(None)  # Signal the thread to stop
    _worker_thread.join()  # Wait for the worker thread to exit
    print("TTS worker stopped gracefully.")


# Start the TTS worker thread
_worker_thread = threading.Thread(target=_tts_worker, daemon=True)
_worker_thread.start()

# Register cleanup for the worker thread
atexit.register(stop_tts_worker)


def totts(text_to_say, session="default"):
    """
    Convert text to speech, save as WAV and MP3, and play the WAV file using pygame.
    
    Args:
        text_to_say (str): The text to convert to speech.
        session (str): Session identifier for file naming.
    """
    wav_path = f"./audio/{session}.wav"


    try:
        # Ensure the audio directory exists
        os.makedirs("./audio", exist_ok=True)

        # Remove existing WAV file if it exists
        if os.path.exists(wav_path):
            os.remove(wav_path)
        # Run the speech synthesis command
        command = f'say.exe -w "{wav_path}" "{text_to_say}"'
        os.system(command)
        
        pygame.init()
        # Play the WAV file using pygame
        pygame.mixer.init()
        pygame.mixer.music.load(wav_path)
        pygame.mixer.music.play()

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        # Cleanup
        pygame.mixer.quit()

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    import time

    # Add test messages
    gotts("Pyro. Said. This is the first test message.")
    time.sleep(1)
    gotts("This is the second test message.")
    time.sleep(1)
    gotts("This is the third test message.")

    # Keep the script running to process the queue
    while not tts_queue.empty():
        time.sleep(0.5)

    print("All messages processed. Exiting.")
