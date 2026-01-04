import ollama
import chromadb
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def getResponse(input):
    apikey = os.getenv('OLLAMA_API_KEY')
    print(apikey)
    client = ollama.Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + os.getenv('OLLAMA_API_KEY')}
    )
    response = client.chat(
        model="gpt-oss:120b-cloud",
        messages=[
            {
                "role": "user",
                "content": input
            }
        ]
    )
    return response

def embed(input):
    response = ollama.embed(
        model="nomic-embed-text:latest",
        input=input
    )
    return response

def initializeChroma():
    client = chromadb.Client()
    collection = client.create_collection(name="docs")
    return collection

def chunk_text(text, chunk_size=1000, chunk_overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks

def process_and_store_document(collection, text, batch_size=20):

    chunks = chunk_text(text)
    print(f"Split document into {len(chunks)} chunks.")
 
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        response = embed(batch)
        embeddings = response["embeddings"]
        
        ids = [str(uuid.uuid4()) for _ in range(len(batch))]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=batch
        )
        print(f"Processed batch {i//batch_size + 1}/{(len(chunks)//batch_size)+1}")

def queryEmbeddings(collection, query):
    response = embed(query)
    result = collection.query(
        query_embeddings=[response["embeddings"][0]],
        n_results=3
    )
    return result

def generateResponse(collection, query):
    result = queryEmbeddings(collection, query)
   
    data = "\n\n".join(result["documents"][0])
    
    prompt = f"Using this data: {data}. Respond to this prompt: {query}"
    response = getResponse(prompt)
    return response
