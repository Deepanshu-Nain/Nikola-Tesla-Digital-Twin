import fitz  # PyMuPDF
import os
import json

def parse_all_pdfs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.abspath(os.path.join(script_dir, "../../data/raw/"))
    output_path = os.path.abspath(os.path.join(script_dir, "../../data/processed/parsed_pages.json"))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    all_pages = []
    
    # Loop through every file in the raw folder
    for filename in os.listdir(raw_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(raw_dir, filename)
            print(f"📄 Parsing: {filename}...")
            
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text("text")
                    
                    # Clean up the text slightly
                    text = text.replace('\n', ' ').strip()
                    
                    if text:
                        all_pages.append({
                            "source": filename, # Keep track of which PDF this came from
                            "page_number": page_num + 1,
                            "text": text
                        })
                doc.close()
            except Exception as e:
                print(f"  [Error] Failed to parse {filename}: {e}")

    print(f"Successfully extracted {len(all_pages)} total pages across all documents.")
    
    # Save the combined data to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_pages, f, indent=4)

if __name__ == "__main__":
    parse_all_pdfs()