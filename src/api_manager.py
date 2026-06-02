import os
import itertools
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_keys = []
for i in range(1, 10): # Supports up to 9 keys
    key = os.environ.get(f"GEMINI_API_KEY_{i}")
    if key:
        api_keys.append(key)

if not api_keys:
    single_key = os.environ.get("GEMINI_API_KEY")
    if single_key:
        api_keys.append(single_key)
    else:
        raise ValueError("No Gemini API keys found in .env!")

print(f"[System] Initialized API Manager with {len(api_keys)} active keys.")

clients = [genai.Client(api_key=k) for k in api_keys]


client_pool = itertools.cycle(clients)

def get_next_client():
    return next(client_pool)