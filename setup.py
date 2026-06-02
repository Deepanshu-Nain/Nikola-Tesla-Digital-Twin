"""
Tesla Digital Twin — Smart Setup Script
----------------------------------------
For MOST users who cloned this repo, the databases are already pre-built
and shipped inside db/. This script will:

  1. Verify your .env file has Gemini API keys.
  2. Check that the pre-built databases exist (qdrant + SQLite).
  3. Check that the Tesla reference voice WAV exists.
  4. Print clear next steps.

Only run the FULL REBUILD (--rebuild flag) if you want to re-index
your own custom PDFs from scratch.
"""

import os
import sys
import subprocess
import argparse

# ── helpers ──────────────────────────────────────────────────────────────────

ROOT = os.path.dirname(os.path.abspath(__file__))

def ok(msg):   print(f"  [OK]  {msg}")
def warn(msg): print(f"  [!]   {msg}")
def err(msg):  print(f"  [ERR] {msg}")
def hdr(msg):  print(f"\n{'='*60}\n  {msg}\n{'='*60}")

def run_script(script_path, description):
    """Run a pipeline script and exit on failure."""
    print(f"\n  >> {description}")
    if not os.path.exists(script_path):
        err(f"Cannot find script: {script_path}")
        sys.exit(1)
    try:
        subprocess.run([sys.executable, script_path], check=True)
        ok(f"{description} — done.")
    except subprocess.CalledProcessError:
        err(f"{description} — FAILED. Stopping pipeline.")
        sys.exit(1)

# ── checks ───────────────────────────────────────────────────────────────────

def check_env():
    """Make sure at least one Gemini API key is configured."""
    hdr("Step 1 — Environment Variables")
    env_path = os.path.join(ROOT, ".env")

    if not os.path.exists(env_path):
        err(".env file not found!")
        print("""
  Fix: copy the template and fill in your key(s):

      cp .env.sample .env          (Mac/Linux)
      copy .env.sample .env        (Windows)

  Then open .env and replace the placeholder values with real keys.
  Get a free key at: https://aistudio.google.com/
""")
        return False

    # Check at least one key is non-placeholder
    found_key = False
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("GEMINI_API_KEY") and "=" in line:
                value = line.split("=", 1)[1].strip()
                if value and "ur api key" not in value.lower() and "api keyy" not in value.lower():
                    found_key = True
                    break

    if found_key:
        ok(".env found with at least one Gemini API key.")
        return True
    else:
        err(".env exists but all keys are still placeholder values.")
        print("\n  Fix: open .env and replace the placeholder text with your real key.\n")
        return False


def check_databases():
    """Verify the pre-built Qdrant and SQLite databases are present."""
    hdr("Step 2 — Pre-built Databases")

    sqlite_path = os.path.join(ROOT, "db", "tesla.db")
    qdrant_path = os.path.join(ROOT, "db", "qdrant", "collection", "tesla_knowledge", "storage.sqlite")

    sqlite_ok = os.path.exists(sqlite_path) and os.path.getsize(sqlite_path) > 0
    qdrant_ok  = os.path.exists(qdrant_path) and os.path.getsize(qdrant_path) > 0

    if sqlite_ok:
        size_kb = os.path.getsize(sqlite_path) // 1024
        ok(f"SQLite database found — tesla.db ({size_kb} KB)")
    else:
        err("tesla.db not found or empty.")

    if qdrant_ok:
        size_kb = os.path.getsize(qdrant_path) // 1024
        ok(f"Qdrant vector store found — storage.sqlite ({size_kb} KB)")
    else:
        err("Qdrant vector store not found or empty.")

    if sqlite_ok and qdrant_ok:
        ok("Both databases ready — no rebuild needed!")
        return True
    else:
        warn("Databases are missing. Run with --rebuild to build from your own PDFs.")
        return False


def check_voice():
    """Check that the Tesla reference voice file exists."""
    hdr("Step 3 — Tesla Reference Voice")

    wav_path = os.path.join(ROOT, "data", "raw_audio", "tesla_reference.wav")

    if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
        size_kb = os.path.getsize(wav_path) // 1024
        ok(f"Reference voice found — tesla_reference.wav ({size_kb} KB)")
        return True
    else:
        warn("tesla_reference.wav not found!")
        print("""
  The voice cloning engine (F5-TTS) needs a reference audio clip of
  Tesla's voice to clone from.

  Fix:
    1. Place a clean WAV file at:  data/raw_audio/tesla_reference.wav
       (mono, 24kHz recommended)

    2. OR if you have an MP3, convert it first:
           python src/convert_audio.py

  Without this file the app will still run but voice output will fail.
""")
        return False


# ── rebuild pipeline ─────────────────────────────────────────────────────────

def run_full_rebuild():
    """Run the complete ingestion pipeline (only needed for custom PDFs)."""
    hdr("FULL REBUILD — Ingestion Pipeline")
    print("  This re-indexes all PDFs in data/raw/ from scratch.")
    print("  It can take 10-30 minutes depending on your API quota.\n")

    raw_dir = os.path.join(ROOT, "data", "raw")
    pdf_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        err(f"No PDFs found in {raw_dir}/")
        print("  Add Tesla PDF documents to data/raw/ before rebuilding.\n")
        sys.exit(1)

    print(f"  Found {len(pdf_files)} PDF(s): {', '.join(pdf_files)}\n")

    steps = [
        ("src/ingest/databases.py",      "1. Initialize SQLite + Qdrant"),
        ("src/ingest/pdf_parser.py",     "2. Parse PDFs → pages JSON"),
        ("src/ingest/chapter_detector.py","3. Detect chapters"),
        ("src/ingest/chunker.py",        "4. Sliding-window chunking"),
        ("src/ingest/enricher.py",       "5. Local AI metadata enrichment (Ollama / Qwen 2.5 3B)"),
        ("src/ingest/vectorizer.py",     "6. Embed + inject into Qdrant"),
    ]

    for rel_path, desc in steps:
        run_script(os.path.join(ROOT, rel_path), desc)

    hdr("REBUILD COMPLETE")
    print("  The knowledge base has been rebuilt with your documents.\n")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tesla Digital Twin — Setup & Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py              # Quick check (recommended for new users)
  python setup.py --rebuild    # Full rebuild from your own PDFs
        """
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Re-run the full ingestion pipeline (only needed for custom PDFs)"
    )
    args = parser.parse_args()

    print("\n  ⚡  Tesla Digital Twin — Setup Validator")
    print("  " + "─" * 44)

    if args.rebuild:
        env_ok = check_env()
        if not env_ok:
            sys.exit(1)
        run_full_rebuild()
        check_voice()
    else:
        env_ok    = check_env()
        db_ok     = check_databases()
        voice_ok  = check_voice()

        hdr("Summary")
        results = [
            ("API Keys (.env)",    env_ok),
            ("Databases (db/)",    db_ok),
            ("Reference voice",    voice_ok),
        ]
        all_good = True
        for label, status in results:
            icon = "OK" if status else "!!"
            print(f"  [{icon}]  {label}")
            if not status:
                all_good = False

        print()
        if env_ok and db_ok:
            print("  ✅ Ready! Start the Digital Twin with:\n")
            print("       python src/app.py\n")
            print("  Then open:  http://127.0.0.1:7860")
            if not voice_ok:
                print("\n  ⚠️  Voice cloning will fail until you add tesla_reference.wav")
        else:
            print("  ❌ Fix the issues above, then run this script again.\n")
        print()


if __name__ == "__main__":
    main()