"""
 wires the Gatekeeper, Memory, Librarian, and Synthesizer  nodes into an operational state machine. the core brain o sthis project.

"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import os
import sys
import time
from google.genai import types
from src.rag.timeline_agent import search_timeline

from src.api_manager import get_next_client

# add project root to sys.path to access custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.rag.librarian import search_tesla_knowledge
from src.persona.tesla_brain import generate_tesla_response
from src.memory.memory_manager import MemoryManager

memory_tool = MemoryManager()

class AgentState(TypedDict):
    """The shared state passed between all nodes in the graph."""
    user_id: str
    user_query: str
    conversation_history: List[dict]
    retrieved_context: str
    user_facts: str
    final_response: str

def gatekeeper_node(state: AgentState):
    """Initial entry point. Prepares the state for processing."""
    print(f"\n[Gatekeeper] Routing query for user: {state['user_id']}")
    # can add dynamic llm routing here . for now just pass it.
    return state

def memory_node(state: AgentState):
    """Retrieves long-term facts about the user from SQLite."""
    print("[Memory] Fetching user facts...")
    facts = memory_tool.get_memories(state["user_id"])
    return {"user_facts": facts}

def librarian_node(state: dict) -> dict:
    print("[Librarian] Searching knowledge base...")
    
    # 1. First, ask the SQL Agent if this is a timeline question
    sql_facts = search_timeline(state["user_query"])
    
    # 2. Then, ask the Qdrant Vector database for general book knowledge
    vector_results = search_tesla_knowledge(state["user_query"], top_k=3)
    
    # Combine both memories
    combined_context = sql_facts + "\n\n"
    for idx, hit in enumerate(vector_results, 1):
        combined_context += f"Document Excerpt {idx} (Chapter: {hit['chapter']}):\n{hit['text']}\n\n"
        
    state["retrieved_context"] = combined_context.strip()
    return state





def synthesizer_node(state: dict) -> dict:
    print("[Synthesizer] Crafting Tesla's response...")
    
    # Extract the necessary data from the graph state
    query = state["user_query"]
    context = state.get("retrieved_context", "")
    history = state.get("conversation_history", [])
    user_facts = state.get("user_facts", "")
    
    # Format the memory into a readable string for the prompt
    history_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-5:]])
    
    prompt = f"""
    You are the brilliant inventor Nikola Tesla. 
    You are speaking out loud to a user in a real-time voice conversation.

    CRITICAL RULES FOR CONCISENESS & COMPLETENESS:
    1. STRICT LENGTH: Your response MUST be between 50 and 80 words maximum.
    2. NO FILLER: Never use introductory fluff like "That is an interesting query" or "Ah, yes". Dive instantly into the core of the answer.
    3. COMPLETE THOUGHTS: Your answer must be a fully resolved, meaningful thought. Do not trail off.
    4. EXACT STRUCTURE: You must synthesize your answer into exactly 3 to 4 punchy sentences:
       - Sentence 1: The direct, factual answer to the query.
       - Sentences 2 & 3: The most fascinating historical detail, mechanical mechanism, or core reasoning.
       - Sentence 4: A sharp, definitive concluding thought.
    
    Relevant Facts about the User: {user_facts}
    
    Recent Conversation History:
    {history_text}
    
    Retrieved Knowledge from your writings:
    {context}
    
    User's New Question: {query}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        client = get_next_client() # Grabs a fresh key
        try:
            # Leaving your original model intact
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            state["final_response"] = response.text
            print("[Synthesizer] Response successfully generated.")
            return state
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                print(f"  [Synthesizer] Key exhausted. Rotating to next key (Attempt {attempt+1}/{max_retries})...")
            else:
                print(f"  [Synthesizer] Error generating response: {e}")
                state["final_response"] = "I apologize, my instruments are experiencing interference."
                return state
                
    state["final_response"] = "The ether is too turbulent. All API keys are currently exhausted."
    return state


workflow = StateGraph(AgentState)

workflow.add_node("gatekeeper", gatekeeper_node)
workflow.add_node("memory", memory_node)
workflow.add_node("librarian", librarian_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("gatekeeper")
workflow.add_edge("gatekeeper", "memory")
workflow.add_edge("memory", "librarian")
workflow.add_edge("librarian", "synthesizer")
workflow.add_edge("synthesizer", END)

app = workflow.compile()
