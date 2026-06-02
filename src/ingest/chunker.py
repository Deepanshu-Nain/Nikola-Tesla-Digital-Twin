"""
 Splits structured document sections into uniform, overlapping text chunks designed for high-accuracy RAG retrieval.
"""

import json
import os

CHUNK_SIZE = 4000
OVERLAP = 200

def generate_chunks():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/chapters.json"))
    output_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/chunks.json"))
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing chapters.json. Run chapter_detector.py first.")
        
    with open(input_path, "r", encoding="utf-8") as f:
        sections = json.load(f)
        
    all_chunks = []
    global_chunk_id = 1
    
    for section in sections:
        doc_name = section["source_document"]
        chapter_title = section["chapter_title"]
        text = section["full_text"]
        
        # Sliding window chunking logic
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end]
            
            all_chunks.append({
                "chunk_id": global_chunk_id,
                "document": doc_name,
                "chapter": chapter_title,
                "text": chunk_text
            })
            
            global_chunk_id += 1
            start += (CHUNK_SIZE - OVERLAP)

    print(f"Created {len(all_chunks)} total chunks across all documents.")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=4)

if __name__ == "__main__":
    generate_chunks()