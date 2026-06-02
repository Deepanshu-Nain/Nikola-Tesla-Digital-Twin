import os
import torch
import soundfile as sf
from f5_tts import api

# The ABSOLUTE PATHS.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../data/audio_outputs"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
REF_AUDIO_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, "../../data/raw_audio/tesla_reference.wav"))
REF_TEXT = "Huh, an interesting query indeed. You ask what I know of you, sir?"

# if you have gpu then lets go as , cpu this whole project is extremely slow , that you cant even test it.
device_type = "GPU" if torch.cuda.is_available() else "CPU"
print(f"[System] Loading F5-TTS on {device_type} for EXACT voice cloning...")

f5tts_engine = api.F5TTS()



# we generate the audio here.
def generate_tesla_audio(text_to_speak: str, chunk_index: int = 0) -> str:
    output_path = os.path.join(OUTPUT_DIR, f"tesla_response_{chunk_index}.wav")
    
    try:
        wav, sample_rate, _ = f5tts_engine.infer(
            ref_file=str(REF_AUDIO_PATH),
            ref_text=REF_TEXT,
            gen_text=text_to_speak,
            nfe_step=8,     # Maximum speed setting for CPU but if you have gpu and its detected just inc this to 16 for better voice quality.
            seed=425,       # Locked voice profile (Tesla og voice )
            speed=1.0       
        )
        sf.write(output_path, wav, sample_rate)
        return output_path
        
    except Exception as e:
        print(f"[Audio] Voice synthesis failed: {e}")
        return None