import subprocess
import os
import sys

def run_script(script_path, description):
    """Executes a Python script and checks for errors."""
    print(f"\n{'='*50}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_path}")
    print(f"{'='*50}")
    
    if not os.path.exists(script_path):
        print(f" ERROR: Cannot find script at {script_path}")
        sys.exit(1)

    try:
        # Run the script and stream the output to the console
        result = subprocess.run([sys.executable, script_path], check=True)
        print(f"\nSUCCESS: {description} completed.\n")
    except subprocess.CalledProcessError as e:
        print(f"\nFAILED: {description} threw an error. Stopping pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we are running from the root of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if the raw directory has ANY PDFs in it
    raw_dir = os.path.join(root_dir, "data/raw/")
    pdf_files = [f for f in os.listdir(raw_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"ERROR: No PDFs found in {raw_dir}. Please add some Tesla documents.")
        sys.exit(1)
        
    print(f" Found {len(pdf_files)} documents to process: {', '.join(pdf_files)}")

    print("\n INITIALIZING TESLA TWIN BUILD PIPELINE ")
    print("This will parse the book, generate embeddings, and build the databases.\n")

    # The exact execution order required to build the brain
    pipeline_steps = [
        ("src/ingest/databases.py", "1. Initializing SQLite and Qdrant Databases"),
        ("src/ingest/pdf_parser.py", "2. Parsing Raw PDF (My Inventions)"),
        ("src/ingest/chapter_detector.py", "3. Detecting and Stitching Chapters"),
        ("src/ingest/chunker.py", "4. Generating Hierarchical Chunks"),
        ("src/ingest/enricher.py", "5. AI Metadata Enrichment (Gemini 2.5 Flash)"),
        ("src/ingest/vectorizer.py", "6. Generating Vectors and Injecting to Qdrant")
    ]

    for script_relative_path, description in pipeline_steps:
        full_path = os.path.join(root_dir, script_relative_path)
        run_script(full_path, description)
        
    print(f"{'='*50}")
    print(" BUILD COMPLETE! The Digital Twin is ready.")
    print("To chat with Tesla, run: python src/app.py")
    print(f"{'='*50}")