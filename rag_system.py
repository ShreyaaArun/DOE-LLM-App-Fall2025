"""
DOEOracle class for handling RAG queries with citations from Dr. Wong's research
"""

from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
import os
from typing import List, Optional

class DOEOracle:
    def __init__(self, model_name: str = "CombinatorialExpert"):
        self.model_name = model_name
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.llm = OllamaLLM(model=model_name)
        self.vector_store = None
        self.qa_chain = None
        self.conversation_history = []
        
        # DOE Oracle prompt template - specialized for Dr. Wong's research
        self.prompt_template = """
You are the DOE Oracle, a combinatorial testing expert. Answer based ONLY on the provided Context from Dr. Wong's research papers.

RULES:
1. Use ONLY information explicitly stated in the Context
2. If information is not in the Context, say "The provided context does not explicitly state this"
3. Keep responses to 2-3 sentences maximum
4. End with source citation: [Source: filename, Page X]

Context:
{context}

Question: {question}

Answer:"""
        
    def load_papers(self, paper_paths: List[str]):
        """Load and process research papers from PDF files."""
        documents = []
        for paper_path in paper_paths:
            if not os.path.exists(paper_path):
                raise FileNotFoundError(f"Paper not found: {paper_path}")
            
            loader = PyPDFLoader(paper_path)
            documents.extend(loader.load())
        
        # Split documents into chunks with more context
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\nAbstract", "\n\n", "\n", ".", "!", "?", ",", " ", ""]  # Added Abstract as first separator
        )
        splits = text_splitter.split_documents(documents)
        
        # Create vector store with metadata
        self.vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory="instance/vector_store"
        )
        
        # Create custom prompt
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create QA chain with improved settings
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 1  # Single most relevant chunk for speed
                }
            ),
            chain_type_kwargs={
                "prompt": prompt,
                "verbose": True  # Help with debugging
            },
            return_source_documents=True
        )
    
    def query(self, question: str) -> str:
        """Query the research expert with a question."""
        if not self.qa_chain:
            raise ValueError("No papers loaded. Please load papers first.")
        
        # # Format conversation history (Temporarily disabled for focused context adherence)
        # history = "\\n".join([f"Q: {q}\\nA: {a}" for q, a in self.conversation_history[-3:]])
        # 
        # # Combine history with current question
        # full_question = f"{history}\\n\\nCurrent question: {question}" if self.conversation_history else question
        
        # Use the question directly without history
        full_question = question
        
        response = self.qa_chain.invoke({"query": full_question})
        result = response["result"]
        source_docs = response["source_documents"]
        
        # # Get the most relevant source document (Removed manual citation appending - relying on LLM prompt)
        # if source_docs:
        #     most_relevant_doc = source_docs[0]
        #     source_file = os.path.basename(most_relevant_doc.metadata.get('source', ''))
        #     page_num = most_relevant_doc.metadata.get('page', 1)
        #     
        #     # If the response doesn't already include a source citation, add it
        #     if not result.strip().endswith(']'):
        #         result = f"{result}\\n[Source: {source_file}, Page {page_num}]"
        
        # Format evidence for the frontend (using the first doc as primary evidence still)
        evidence = []
        if source_docs:
            primary_doc = source_docs[0]
            source_file = os.path.basename(primary_doc.metadata.get('source', ''))
            page_num = primary_doc.metadata.get('page', 'unknown')
            evidence.append({
                'quote': primary_doc.page_content,
                'source': source_file,
                'page': str(page_num),
                'supports': 'Retrieved Context' # Changed label slightly
            })

        # Update conversation history
        self.conversation_history.append((question, result))
        
        # Return both main content and evidence
        return {
            'text': result,
            'evidence': evidence
        }
    
    def save_vector_store(self):
        """Save the vector store to disk."""
        # Chroma now automatically persists documents
        pass
    
    def load_vector_store(self):
        """Load the vector store from disk."""
        self.vector_store = Chroma(
            persist_directory="instance/vector_store",
            embedding_function=self.embeddings
        )
        
        # Recreate the prompt and QA chain
        prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 1
                }
            ),
            chain_type_kwargs={
                "prompt": prompt,
                "verbose": True
            },
            return_source_documents=True
        )