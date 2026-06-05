import os
import torch
import numpy as np
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


def concatenate_audio_files(paths: list, output_filename: str = "tesla_full_response.wav") -> str:
    """
    Merge a list of WAV file paths into a single WAV file.
    All files must share the same sample rate (guaranteed since they all
    come from the same F5-TTS engine call).
    Returns the path to the merged file, or None if the list is empty.
    """
    valid_paths = [p for p in paths if p and os.path.exists(p)]
    if not valid_paths:
        return None

    arrays = []
    sample_rate = None
    for p in valid_paths:
        data, sr = sf.read(p, dtype="float32")
        sample_rate = sr
        arrays.append(data)

    # Add a short 150ms silence between sentences for natural pacing
    silence = np.zeros(int(sample_rate * 0.15), dtype="float32")
    merged = arrays[0]
    for chunk in arrays[1:]:
        merged = np.concatenate([merged, silence, chunk])

    output_path = os.path.join(OUTPUT_DIR, output_filename)
    sf.write(output_path, merged, sample_rate)
    return output_path