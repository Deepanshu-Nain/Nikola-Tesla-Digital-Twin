import os
import time
from qdrant_client import QdrantClient
from google import genai
from google.genai import types
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

from src.api_manager import get_next_client


# Load configurations
load_dotenv()


# Initialize the Cross-Encoder model specified in the architecture
print("[System] Loading MS-MARCO Cross-Encoder Model...")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def expand_query(query: str, max_retries: int = 3) -> str:
    prompt = f"..." # Keep your existing prompt here
    
    for attempt in range(max_retries):
        client = get_next_client() # Grabs a fresh key for every attempt
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                print(f"  [Librarian] Key exhausted. Instantly rotating to next key (Attempt {attempt+1}/{max_retries})...")

            else:
                print(f"  [Librarian] Expansion failed. Error: {e}")
                return query
    return query

def embed_query(query: str, max_retries: int = 3) -> list[float]:
    for attempt in range(max_retries):
        client = get_next_client()
        try:
            result = client.models.embed_content(
                model="gemini-embedding-2",
                contents=query,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            return result.embeddings[0].values
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                print(f"  [Librarian] Key exhausted. Instantly rotating to next key (Attempt {attempt+1}/{max_retries})...")
            else:
                raise e
    raise Exception("Failed to embed query after max retries across all keys.")

def search_tesla_knowledge(query: str, top_k: int = 3) -> list[dict]:
    """
    Advanced RAG Pipeline: Query Expansion -> Qdrant Search -> Cross-Encoder Reranking
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    qdrant_path = os.path.abspath(os.path.join(script_dir, "../../db/qdrant/"))
    
    client = QdrantClient(path=qdrant_path)
    collection_name = "tesla_knowledge"
    
    print(f"\n[Librarian] Original Query: '{query}'")
    
    # Step 1: Query Expansion
    expanded_query = expand_query(query)
    
    # Step 2: Embed Query
    query_vector = embed_query(expanded_query)
    
    # Step 3: Broad Qdrant Search (Fetch top 15 instead of top 3)
    broad_results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=15
    ).points
    
    if not broad_results:
        return []
        
    # Step 4: Cross-Encoder Reranking
    cross_inp = [[query, hit.payload.get("text", "")] for hit in broad_results]
    cross_scores = reranker.predict(cross_inp)
    
    # Safely pair the hits with their cross-encoder scores
    scored_points = list(zip(broad_results, cross_scores))
    
    # Sort the paired list based on the cross-encoder score in descending order
    scored_points.sort(key=lambda x: x[1], reverse=True)
    
    # Step 5: Extract only the absolute Top K points from our sorted pairs
    final_top_results = [item[0] for item in scored_points[:top_k]]
    
    formatted_results = []
    for hit in final_top_results:
        payload = hit.payload
        formatted_results.append({
            "chapter": payload.get("chapter", "Unknown"),
            "text": payload.get("text", "")
        })
        
    print(f"[Librarian] Successfully retrieved and reranked top {top_k} chunks.")
    return formatted_results