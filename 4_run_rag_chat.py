import os
import chromadb
from chromadb.utils import embedding_functions
import ollama

# ---------------------------------------------------------
# 1. Initialize Vector Database (Retrieval Engine)
# ---------------------------------------------------------
print("Loading Vector Database (ChromaDB)...")
db_path = "./chroma_db"
client = chromadb.PersistentClient(path=db_path)
embedding_func = embedding_functions.DefaultEmbeddingFunction()

# Connect to the collection we built
collection_name = "dating_psychology_knowledge"
collection = client.get_collection(
    name=collection_name, 
    embedding_function=embedding_func
)
print(f"✅ Successfully loaded {collection.count()} chunks of knowledge.")

# ---------------------------------------------------------
# 2. Main Chat Loop (Generation Engine)
# ---------------------------------------------------------
print("\n" + "="*50)
print("🧠 OFFLINE AI PSYCHOLOGY ADVISOR (Gemma 4 RAG)")
print("Type 'quit' or 'exit' to close the chat.")
print("="*50 + "\n")

MODEL_NAME = "gemma4:latest"

while True:
    # 1. Get User Input
    user_question = input("\n🧑‍💻 You: ")
    
    if user_question.lower() in ["quit", "exit"]:
        print("Goodbye!")
        break
        
    if not user_question.strip():
        continue
        
    print(f"\n🔍 Searching vector database for relevant advice...")
    
    # 2. Retrieve Context from ChromaDB
    results = collection.query(
        query_texts=[user_question],
        n_results=3  # Get top 3 most relevant paragraphs
    )
    
    retrieved_chunks = results["documents"][0]
    sources = [meta["source"] for meta in results["metadatas"][0]]
    
    # Bundle the chunks into a unified context string
    context_text = "\n\n--- NEXT CHUNK ---\n\n".join(retrieved_chunks)
    
    # 3. Build the RAG Prompt
    system_prompt = f"""You are a top-tier dating and psychology advisor. 
You possess deep psychological knowledge on male/female dynamics.

CRITICAL INSTRUCTION: You must base your advice strictly on the "Provided Context" below. Do not give generic advice or invent strategies that contradict the context. If the context does not contain the exact answer, use its principles to formulate the best advice possible. 

Provided Context:
{context_text}
"""
    
    # 4. Generate with Ollama
    print(f"🤖 Gemma 4 (Sources: {', '.join(set(sources))}):")
    print("-" * 50)
    
    try:
        stream = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_question}
            ],
            stream=True
        )
        
        # Stream the output directly to the terminal!
        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)
            
    except Exception as e:
        print(f"\n[ERROR: Make sure Ollama app is running locally! Exception: {e}]")
        
    print("\n" + "-" * 50)
