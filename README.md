# 🥧 Pye.ai: No-Code AI Customer Support Platform

![Status](https://img.shields.io/badge/Status-Beta_Live-success)
![Architecture](https://img.shields.io/badge/Architecture-RAG_Pipeline-purple)
![Stack](https://img.shields.io/badge/Stack-Python_|_Django_|_OpenAI-green)

> **"Build a smart support agent in minutes, not months."**
> Pye.ai is a No-Code platform that allows businesses to build, train, and deploy custom AI customer support agents using their own data (PDFs, Databases, Website links).

---

## 🤖 Project Overview

Most AI chatbots hallucinate or don't know specific company details. **Pye.ai** solves this using **RAG (Retrieval-Augmented Generation)**.

It provides a visual dashboard where non-technical users can upload their knowledge base, and the system automatically converts that data into a "brain" for the AI. The result is a customer support bot that answers questions accurately based *only* on the provided data.

---

## 🏗️ Technical Architecture

The platform is built on two core pillars: The **Prompt Studio** and the **Data Ingestion Engine**.

### 1. The LLM/Prompt Editor Studio
I built a "VS Code-like" experience for prompt engineering integrated directly into the Django view layer.
* **System Prompt Configuration:** Users can define the bot's persona (e.g., "You are a helpful medical assistant" vs "You are a sarcastic IT guy") via a simple UI.
* **Temperature & Top-P Control:** Python abstraction layers allow users to adjust the "creativity" of the AI models dynamically.
* **Real-time Testing:** A split-screen playground where users can chat with the bot immediately after tweaking the prompt to verify behavior.

### 2. RAG Implementation ("The Training Phase")
This is the core engine that makes the bot "smart." When a user uploads a file, the following pipeline executes:

1.  **Ingestion:** The **Django backend** accepts multiple formats (PDF, DOCX, CSV, SQL Dumps) using Python libraries like `pypdf` and `pandas`.
2.  **Chunking:** The text is split into semantic chunks (e.g., 500 characters with overlap) using Python's `RecursiveCharacterTextSplitter` to ensure context is preserved.
3.  **Embedding:** Each chunk is passed through an Embedding Model (e.g., `text-embedding-3-small`) to convert text into high-dimensional vectors.
4.  **Vector Storage:** These vectors are stored in a dedicated Vector Database (e.g., Pinecone/Weaviate/pgvector), indexed for fast similarity search.



[Image of RAG architecture diagram]

<div align="center">
  <img src="./assets/Advanced-RAG.png" alt="RAG" width="800"  >
  <p><em>Figure 1: RAG architecture diagram.</em></p>
</div>
---

## 🧠 How the Query Works (Runtime)

When a customer asks a question on the frontend widget:
1.  **Vector Search:** The system converts the user's question into a vector and queries the database for the most similar "chunks" of knowledge.
2.  **Context Injection:** These chunks are injected dynamically into the LLM's context window via the Django view logic.
3.  **Generation:** The AI answers the question using *only* the retrieved facts.

---

## 🛠️ Tech Stack

* **Core Framework:** `Django` (Python) - Handles Auth, API, and View Logic.
* **UI/Templates:** `Django Templates` / `HTML5` / `JavaScript` (Interactive Dashboard).
* **AI Engine:** `OpenAI Python SDK` (ChatCompletion & Embeddings).
* **Data Processing:** `Pandas` & `NumPy` (For efficient file manipulation before embedding).
* **Database:** `PostgreSQL` (User auth, Project settings) + `Vector DB` (Knowledge base).
* **Orchestration:** `LangChain` (Python) for managing chat history chains and memory.

---

## 👨‍💻 Developer Role

**Tunde Oluwamo**
*Full Stack Developer & AI Architect*
[LinkedIn Profile](https://linkedin.com/in/oluwamo-shadrach-740242185)