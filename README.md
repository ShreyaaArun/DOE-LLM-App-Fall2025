# UT Dallas Software Engineering Capstone Project
## Group 4 - Spring 2025

# DOE Oracle LLM - Combinatorial Testing Research Assistant

> **A specialized AI system for querying Dr. Wong's combinatorial testing research papers**

## Overview

The **DOE Oracle LLM** is an intelligent research assistant that uses **Retrieval-Augmented Generation (RAG)** to answer questions about combinatorial testing based exclusively on Dr. Wong's research papers. It combines a custom fine-tuned model with a vector database of research content to provide accurate, citation-backed responses.

### Key Features
- **Research-Grounded Responses** - Only answers based on the provided research papers
- **Citation Support** - Every response includes source citations with page numbers
- **Custom CombinatorialExpert Model** - Specialized for combinatorial testing domain
- **Modern Web Interface** - Clean, responsive React frontend
- **Fast Performance** - Optimized for quick responses

---

## Quick Start Guide

### Prerequisites

Before you begin, ensure you have:
- **Python 3.8+** installed
- **Git** installed
- **Windows, macOS, or Linux** (these instructions cover all platforms)

---

### 1. **Clone the Repository**

```bash
git clone https://github.com/mloganu717/DOE-Oracle-LLM.git
cd DOE-Oracle-LLM
```

---

### 2. **Install Ollama** - **CRITICAL REQUIREMENT**

The system **requires Ollama** to run the language models locally.

#### **Windows:**
1. Download from: https://ollama.com/download
2. Run the installer
3. Ollama will start automatically

#### **macOS:**
```bash
# Using Homebrew (recommended)
brew install ollama

# Or download from: https://ollama.com/download
```

#### **Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Verify Installation:**
```bash
ollama --version
```

---

### 3. **Download Required Models**

Pull the necessary language models (this may take several minutes):

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

**Expected Download Sizes:**
- `llama3.2`: ~2GB
- `nomic-embed-text`: ~274MB

---

### 4. **Set Up Python Environment**

#### **Windows:**
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

#### **macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**You should see `(venv)` in your terminal prompt**

---

### 5. **Install Dependencies**

```bash
pip install -r requirements.txt
```

**Key packages being installed:**
- Flask (web framework)
- LangChain (RAG system)
- ChromaDB (vector database)
- Ollama (model interface)

---

### 6. **Create the Custom Model**

This creates the specialized **CombinatorialExpert** model:

```bash
python setup_combinatorial_model.py
```

**Expected output:**
```
Setting up CombinatorialExpert model for Dr. Wong's research
============================================================
Ollama is installed and running
Base model llama3.2 is available
Embedding model nomic-embed-text is available
CombinatorialExpert model created successfully
Setup completed successfully!
```

---

### 7. **Start the Backend Server**

```bash
flask --app doe run --debug
```

**Success indicators:**
- You should see: `* Running on http://127.0.0.1:5000`
- Message: `Loading existing vector store...`
- Message: `Vector store loaded successfully.`

**First-time startup:** The system will process the research papers and create a vector database. This may take 1-2 minutes on first run.

---

### 8. **Start the Frontend** (Optional but Recommended)

Open a **new terminal window** and navigate to the frontend:

```bash
cd doe-frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:5173

---

## Usage

### **Backend Only (API)**
- Access the API at: http://localhost:5000
- Test endpoint: `POST /api/search` with JSON: `{"query": "What is combinatorial testing?"}`

### **Full Application (Frontend + Backend)**
- Open your browser to: http://localhost:5173
- Ask questions about combinatorial testing research
- Receive answers with citations and source references

---

## Project Structure

```
DOE-Oracle-LLM/
├── doe/                          # Backend Flask application
├── doe-frontend/                 # React frontend
├── instance/
│   ├── research_papers/          # Dr. Wong's research PDFs
│   ├── vector_store/             # Processed vector database
│   └── knowledge/                # Model configurations
├── rag_system.py                 # Core RAG implementation
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Troubleshooting

### **Common Issues:**

#### "Ollama not found"
**Solution:** Ensure Ollama is installed and running:
```bash
ollama serve  # Start Ollama manually if needed
```

#### "Model not found: CombinatorialExpert"
**Solution:** Re-run the model creation:
```bash
python setup_combinatorial_model.py
```

#### "Virtual environment not activated"
**Solution:** Make sure you see `(venv)` in your prompt:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### "Slow responses (30+ seconds)"
This is normal for the first few queries as the system loads. Subsequent queries should be faster (5-10 seconds).

---

## Contributing

When working on this project:

1. **Always activate the virtual environment first**
2. **Keep Ollama running** in the background
3. **Test both backend and frontend** after changes
4. **Check the terminal logs** for any errors

---

## Support

If you encounter issues:

1. Check the **terminal output** for error messages
2. Verify **Ollama is running**: `ollama list`
3. Confirm **models are available**: Should see `CombinatorialExpert` and `llama3.2`
4. Ensure **virtual environment is active**: Look for `(venv)` in prompt

---

## Success Checklist

- [ ] Ollama installed and running
- [ ] Models downloaded (`llama3.2`, `nomic-embed-text`)
- [ ] CombinatorialExpert model created
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Backend server running on port 5000
- [ ] Can ask questions and receive research-based answers

**If all items are checked, you're ready to explore combinatorial testing research with the DOE Oracle!**
