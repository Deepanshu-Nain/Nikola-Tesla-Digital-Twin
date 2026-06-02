"""
 Generates embeddings using Gemini API with built-in rate limit
handling and injects the chunks into the Qdrant database.
"""

import os
import json
import time
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
ai_client = genai.Client()

def generate_embedding(text_to_embed: str, max_retries: int = 5) -> list[float]:
    """Generates a vector embedding with a retry loop for API rate limits."""
    for attempt in range(max_retries):
        try:
            result = ai_client.models.embed_content(
                model="gemini-embedding-2",
                contents=text_to_embed,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            return result.embeddings[0].values
            
        except Exception as e:
            error_str = str(e).lower()
            # If we hit a 429 Quota or 503 Busy error, back off and try again
            if "429" in error_str or "quota" in error_str or "503" in error_str or "unavailable" in error_str:
                wait_time = (attempt + 1) * 15  # Wait .
                print(f"  [API Rate Limit Hit] Pausing for {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print(f"  [Error] Failed to generate embedding: {e}")
                raise e
                
    raise Exception("Failed to generate embedding after maximum retries. API limit may be exhausted for the day.")

def inject_vectors():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/enriched_chunks.json"))
    qdrant_path = os.path.abspath(os.path.join(script_dir, "../../db/qdrant/"))

    if not os.path.exists(input_path):
        raise FileNotFoundError("enriched_chunks.json not found. Run enricher.py first.")

    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    client = QdrantClient(path=qdrant_path)
    collection_name = "tesla_knowledge"

    # Check if collection exists; if not, create it
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )

    print(f"Beginning vector injection for {len(chunks)} chunks into '{collection_name}'...")

    points = []
    for i, chunk in enumerate(chunks, 1):
        print(f"Embedding chunk {i} / {len(chunks)}...")

        # Create a rich searchable string containing both text and metadata
        metadata = chunk.get("metadata", {})
        searchable_context = f"Chapter: {chunk.get('chapter', 'Unknown')}\nText: {chunk['text']}\nKeywords: {', '.join(metadata.get('keywords', []))}"

        vector = generate_embedding(searchable_context)

        points.append(
            PointStruct(
                id=chunk["chunk_id"],
                vector=vector,
                payload={
                    "document": chunk.get("document", "Unknown"),
                    "chapter": chunk.get("chapter", "Unknown"),
                    "text": chunk["text"],
                    "metadata": metadata
                }
            )
        )
        
        
        time.sleep(4.5)

    print("Uploading vectors to Qdrant...")
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(" Vector injection complete!")

if __name__ == "__main__":
    inject_vectors()