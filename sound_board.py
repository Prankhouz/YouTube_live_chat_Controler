import pygame
import os

#os.environ["SDL_AUDIODRIVER"] = "dummy" (Only needed when running in VS Code Server (in VS Studio this needs to be commented))

# Initialize Pygame
pygame.init()

# Initialize the mixer, you may need to tweak the buffer size for optimal performance
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)

# Dictionary to map sound names to their respective files
sounds = {
    "applause": "sounds/claps.mp3",
    "boo": "sounds/boo.mp3",
    "mc": "sounds/mc.MP3",
    "crunch": "sounds/crunch.mp3",
    "itsfine": "sounds/itsfine.mp3",
    "subscribe": "sounds/subscribe.mp3",
    "ifallgoeswell": "sounds/ifallgoeswell.mp3",
    "therewego": "sounds/therewego.mp3",
    "howdoiusethis": "sounds/howdoiusethis.mp3",
    "wobble": "sounds/wobble.mp3",
    "taskcomplete": "sounds/taskcomplete.mp3",
    # Add more sounds here
}


def play_sound(sound_name):
    try:
        # Retrieve the file path from the dictionary using the sound name
        sound_file = sounds[sound_name]

        # Load the sound
        sound = pygame.mixer.Sound(sound_file)

        # Play the sound
        sound.play()

        # Wait for the sound to finish playing
        while pygame.mixer.get_busy():
            pygame.time.wait(100)
    except KeyError:
        print(f"No sound found for '{sound_name}'")
    except Exception as e:
        print(f"Error playing sound: {e}")
