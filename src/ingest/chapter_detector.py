"""
Groups parsed pages by explicit chapter headers 
"""

import json
import os
import re

def detect_chapters_and_documents():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/parsed_pages.json"))
    output_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/chapters.json"))
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing parsed_pages.json. Run pdf_parser.py first.")
        
    with open(input_path, "r", encoding="utf-8") as f:
        pages = json.load(f)
        
    structured_documents = {}
    
    # Simple regex to check for traditional chapters (e.g., CHAPTER I, CHAPTER 1)
    chapter_regex = re.compile(r'\b(CHAPTER\s+[IVXLCDM]+|\bCHAPTER\s+\d+)\b', re.IGNORECASE)

    for page in pages:
        doc_name = page["source"]
        text = page["text"]
        
        if doc_name not in structured_documents:
            structured_documents[doc_name] = {}
            
        # try to see if this specific page introduces a new chapter
        match = chapter_regex.search(text)
        
        if match:
            current_chapter = match.group(1).upper()
        else:
            # if no chapter exists in the file yet, default to the file name
            current_chapter = structured_documents[doc_name].get("last_seen", "Introduction / Main Text")
            
        if current_chapter not in structured_documents[doc_name]:
            structured_documents[doc_name][current_chapter] = []
            
        structured_documents[doc_name][current_chapter].append(text)
        structured_documents[doc_name]["last_seen"] = current_chapter

    # format the data into a clean list of chunker to read.
    final_output = []
    for doc_name, chapters in structured_documents.items():
        for ch_title, text_list in chapters.items():
            if ch_title == "last_seen":
                continue
            final_output.append({
                "source_document": doc_name,
                "chapter_title": ch_title,
                "full_text": " ".join(text_list)
            })

    print(f" Processed sections: Found {len(final_output)} distinct document sections.")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

if __name__ == "__main__":
    detect_chapters_and_documents()