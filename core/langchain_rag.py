from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

from sentence_transformers import SentenceTransformer
from langchain.schema.messages import AIMessage, HumanMessage

import pandas as pd
import os

# Config
embedding_model_name = "all-MiniLM-L6-v2"
FAISS_PATH = "rag_index"

# Embedding model
embedder = HuggingFaceEmbeddings(model_name=embedding_model_name)

llm = ChatOllama(model="mistral")
# llm = ChatOllama(model="gemma:2b",timeout=120)



# Shared in-memory conversation (can switch to per-user later)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Global FAISS vectorstore reference
vectorstore = None

# Load and embed CSV into FAISS, then save it to disk
def load_csv_into_faiss(csv_path):
    global vectorstore
    df = pd.read_csv(csv_path)
    texts = []

    for _, row in df.iterrows():
        doc = (
            f"Property Address: {row['Property Address']}, "
            f"Suite: {row['Suite']}, Floor: {row['Floor']}, Size: {row['Size (SF)']} SF, "
            f"Rent: ${row['Rent/SF/Year']} per SF/year, Annual: ${row['Annual Rent']}, Monthly: ${row['Monthly Rent']}, "
            f"GCI for 3 Years: ${row['GCI On 3 Years']}, "
            f"Associates: {row['Associate 1']}, {row['Associate 2']}, {row['Associate 3']}, {row['Associate 4']}, "
            f"Email: {row['BROKER Email ID']}"
        )
        texts.append(doc)

    # Create and save vectorstore
    print("[DEBUG] First embedded document sample:")
    print(texts[0])

    vectorstore = FAISS.from_texts(texts, embedding=embedder)
    vectorstore.save_local(FAISS_PATH)
    print(f"[INFO] FAISS vectorstore saved to {FAISS_PATH}")

# Load chain with memory and retriever
def get_chain():
    global vectorstore

    if not vectorstore:
        if os.path.exists(f"{FAISS_PATH}/index.faiss"):
            print("[INFO] Loading FAISS vectorstore from disk...")
            print(FAISS_PATH)
            vectorstore = FAISS.load_local(
                FAISS_PATH,
                embeddings=embedder,
                allow_dangerous_deserialization=True
            )

        else:
            raise Exception("Vectorstore is not initialized. Upload docs first.")

    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory
    )

    return chain

