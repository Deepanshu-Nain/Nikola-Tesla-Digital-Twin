"""
Voice-to-Voice Interface for Tesla Digital Twin
Author: Deepanshu Nain (Roll No: 25/B01/045)
Description: Integrated GPU-accelerated voice synthesis with Gradio 6.0 UI.
"""

import sys
import os
import re
import gradio as gr
from dotenv import load_dotenv

# Force Python to recognize the root project directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agents.graph import app as tesla_graph
from src.audio.voice_generator import generate_tesla_audio
from src.api_manager import get_next_client

def process_voice_interaction(audio_filepath, chat_history):
    if not audio_filepath:
        yield chat_history, gr.update(value=None)
        return
        
    try:
        print(f"\n[Audio System] Transcribing user speech via Gemini...")
        
        # 1. Speech-to-Text
        client = get_next_client()
        audio_file = client.files.upload(file=audio_filepath)
        transcription_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                audio_file, 
                "Transcribe exactly what the user is saying in this audio clip."
            ]
        )
        user_text_query = transcription_response.text.strip()
        print(f"[Audio System] User Spoke: '{user_text_query}'")
        client.files.delete(name=audio_file.name)
        
        # 2. Run LangGraph RAG
        initial_state = {
            "user_query": user_text_query,
            "user_id": "Deepanshu Nain", 
            "conversation_history": chat_history,
            "user_facts": "",
            "retrieved_context": "",
            "final_response": ""
        }
        
        final_state = tesla_graph.invoke(initial_state)
        full_reply_text = final_state["final_response"]
        
        # Dictionary format for Gradio 6.0
        chat_history.append({"role": "user", "content": user_text_query})
        chat_history.append({"role": "assistant", "content": full_reply_text})
        yield chat_history, gr.update(value=None)
        
        # 3. Stream audio
        sentences = re.split(r'(?<=[.!?]) +', full_reply_text)
        for index, sentence in enumerate(sentences):
            if not sentence.strip(): continue
            audio_chunk_path = generate_tesla_audio(sentence.strip(), chunk_index=index)
            yield chat_history, gr.Audio(value=audio_chunk_path, autoplay=True)

    except Exception as e:
        print(f"[Audio System] Flow error: {e}")
        chat_history.append({"role": "assistant", "content": "My instruments are struggling to capture your frequency. Could you try speaking again?"})
        yield chat_history, gr.update(value=None)


def process_text_interaction(user_text_message, chat_history):
    if not user_text_message.strip():
        yield "", chat_history, gr.Audio(value=None)
        return
        
    initial_state = {
        "user_query": user_text_message,
        "user_id": "Deepanshu Nain",
        "conversation_history": chat_history,
        "user_facts": "",
        "retrieved_context": "",
        "final_response": ""
    }
    
    final_state = tesla_graph.invoke(initial_state)
    full_reply_text = final_state["final_response"]
    
    chat_history.append({"role": "user", "content": user_text_message})
    chat_history.append({"role": "assistant", "content": full_reply_text})
    yield "", chat_history, gr.Audio(value=None)
    
    sentences = re.split(r'(?<=[.!?]) +', full_reply_text)
    for index, sentence in enumerate(sentences):
        if not sentence.strip(): continue
        audio_chunk_path = generate_tesla_audio(sentence.strip(), chunk_index=index)
        yield "", chat_history, gr.Audio(value=audio_chunk_path, autoplay=True)

# --- UI Setup ---
with gr.Blocks(title="Tesla Digital Twin") as demo:
    gr.Markdown("# ⚡ Nikola Tesla Digital Twin")
    
    with gr.Row():
        with gr.Column(scale=3):
            # FIXED: type="messages" is required for Gradio 6.0
            chatbot = gr.Chatbot(height=500, type="messages", label="Tesla")
            text_input = gr.Textbox(placeholder="Ask your question...", label="Input")
            
        with gr.Column(scale=1):
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Mic Input")
            audio_output = gr.Audio(label="Tesla's Response", autoplay=True, visible=True)
            stop_btn = gr.Button("🛑 Interrupt", variant="stop")

    # Interruption Protocol
    voice_event = audio_input.stop_recording(
        fn=process_voice_interaction,
        inputs=[audio_input, chatbot],
        outputs=[chatbot, audio_output]
    )
    text_event = text_input.submit(
        fn=process_text_interaction,
        inputs=[text_input, chatbot],
        outputs=[text_input, chatbot, audio_output]
    )
    audio_input.start_recording(fn=lambda: None, cancels=[voice_event, text_event])
    stop_btn.click(fn=lambda: None, cancels=[voice_event, text_event])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)