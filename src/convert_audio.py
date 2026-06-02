
import os
from pydub import AudioSegment

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


MP3_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/raw_audio/tesla_reference.mp3"))
WAV_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "../data/raw_audio/tesla_reference.wav"))

print("[System] Converting MP3 to 24kHz Mono WAV...")
try:
    audio = AudioSegment.from_mp3(MP3_PATH)
    audio = audio.set_frame_rate(24000).set_channels(1)
    audio.export(WAV_PATH, format="wav")
    print(f"[Success] Pristine WAV generated at: {WAV_PATH}")
    print("You can now safely delete the original MP3 file!")
except Exception as e:
    print(f"[Error] Conversion failed: {e}")





    """
    this was required , as i wanted to the agent /tesla sound exactaly like tesla no ai voice over from tts.
    """