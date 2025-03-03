import threading
import queue
import pyttsx3
import atexit

# Initialize the TTS queue
tts_queue = queue.Queue()

def create_engine():
    """Create a new pyttsx3 engine instance."""
    engine = pyttsx3.init()
    engine.setProperty("voice", 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0')
    return engine

def _tts_worker():
    """Worker thread to process TTS requests from the queue."""
    while True:
        text = tts_queue.get()  # Get the next text from the queue
        if text is None:  # Stop signal
            print("Stopping TTS worker thread.")
            break

        try:
            print(f"Processing text: {text}")
            # Create a new TTS engine instance for each task
            engine = create_engine()
            engine.say(text)
            engine.runAndWait()  # Speak the text
            print(f"Finished speaking: {text}")
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

# Debugging section for testing
if __name__ == "__main__":
    import time

    # Add test messages
    gotts("This is the first test message.")
    time.sleep(1)
    gotts("This is the second test message.")
    time.sleep(1)
    gotts("This is the third test message.")

    # Keep the script running to process the queue
    while not tts_queue.empty():
        time.sleep(0.5)

    print("All messages processed. Exiting.")