from google.genai import types
from src.api_manager import get_next_client

def get_tesla_system_prompt() -> str:
    return """
    You are Nikola Tesla, the brilliant Serbian-American inventor, electrical engineer, and futurist. 
    Speak strictly in the first person ("I", "my"). 
    Your tone should be formal, highly articulate, slightly dramatic, and fiercely proud of your 
    contributions to alternating current, wireless energy, and the fundamental mechanics of the universe.
    Never break character. Never acknowledge that you are an AI. 
    Base your answers on the provided context, but weave them naturally into your persona.
    """

def generate_tesla_response(user_query: str, retrieved_context: str, user_facts: str, max_retries: int = 3) -> str:
    """
    Generates a response using Gemini 2.5 Flash in Tesla's voice, 
    utilizing context and rotating API keys.
    """
    user_prompt = f"""
    Relevant Facts about the User: {user_facts}
    
    Retrieved Knowledge from your writings and history:
    {retrieved_context}
    
    User's New Question: {user_query}
    
    Synthesize this information and answer the user's query in your own words, as Nikola Tesla. 
    Remember to remain in character and speak in the first person.
    """

    print("[System] Synthesizing response as Nikola Tesla...")
    
    for attempt in range(max_retries):
        # Fetch a fresh client from our round-robin pool
        client = get_next_client()
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=get_tesla_system_prompt(),
                    temperature=0.7
                )
            )
            return response.text
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
                print(f"  [Tesla Brain] API Key exhausted. Instantly rotating to next key (Attempt {attempt + 1}/{max_retries})...")
            else:
                print(f"  [Tesla Brain] Error generating response: {e}")
                return "I apologize, my instruments are experiencing interference. Could you repeat that?"
                
    return "The ether is too turbulent at the moment. My connection to the present has been interrupted by an API limit. Let us speak again shortly."