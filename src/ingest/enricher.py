"""
 Uses a LOCAL model (Ollama - Qwen 2.5 3B) to extract structured metadata from text chunks
"""

import json
import os
from pydantic import BaseModel
import ollama

class TeslaMetadata(BaseModel):
    summary: str
    keywords: list[str]
    inventions: list[str]
    scientific_topics: list[str]
    historical_period: str
    notable_people: list[str]
    hypothetical_questions: list[str]
    speaking_style_notes: str
    confidence_score: float

def enrich_chunk_locally(chunk_text: str) -> dict:
    """Passes the chunk to local Qwen 2.5 for fast, free JSON extraction."""
    
    # Extract the schema definition for the prompt
    schema_str = TeslaMetadata.model_json_schema()
    
    prompt = f"""
    Analyze the following text from Nikola Tesla's autobiography 'My Inventions'.
    Extract the metadata and format it strictly according to the provided JSON schema.
    
    JSON Schema Requirements:
    {json.dumps(schema_str)}
    
    Text Chunk:
    {chunk_text}
    """
    
    try:
        # Calls the local Qwen 2.5 3B model
        response = ollama.chat(
            model='qwen2.5:3b', 
            messages=[
                {
                    'role': 'system', 
                    'content': 'You are an expert data extraction API. You must output ONLY valid, raw JSON that perfectly matches the requested schema. Do not include markdown formatting like ```json.'
                },
                {'role': 'user', 'content': prompt}
            ], 
            format='json' # Enforces JSON output at the Ollama engine level
        )
        
        return json.loads(response['message']['content'])
        
    except Exception as e:
        print(f"  [Error] Local enrichment failed: {e}")
        # Fallback to empty schema if extraction fails
        return TeslaMetadata(
            summary="Error processing chunk", keywords=[], inventions=[], 
            scientific_topics=[], historical_period="", notable_people=[], 
            hypothetical_questions=[], speaking_style_notes="", confidence_score=0.0
        ).model_dump()

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/chunks.json"))
    output_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/enriched_chunks.json"))
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)
        
    enriched_data = []
    print(f"Starting LOCAL enrichment for {len(raw_chunks)} chunks using Qwen 2.5 (3B)...")
    
    for chunk in raw_chunks:
        print(f"Processing chunk {chunk['chunk_id']} / {len(raw_chunks)}...")
        metadata = enrich_chunk_locally(chunk['text'])
        enriched_chunk = {**chunk, "metadata": metadata}
        enriched_data.append(enriched_chunk)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=4)
        
    print(f"Saved enriched chunks to {output_path}. Local processing complete!")