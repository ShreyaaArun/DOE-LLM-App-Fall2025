import os
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from flask import current_app
import logging
import time

class Mediator:
    """Mediator class to facilitate interaction with Ollama using RAG"""

    def __init__(self, model_name="llama3"):
        # Initialize language model (LLM)
        self.llm = ChatOllama(model=model_name)
        self.embeddings = OllamaEmbeddings(model=model_name)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # Placeholder for vector_db, retriever, and chain
        self.vector_db = None
        self.retriever = None
        self.chain = None

    def process_papers(self):
        """Process research papers and create vector store"""
        papers_dir = current_app.config['RESEARCH_PAPERS']
        vector_store_path = current_app.config['VECTOR_STORE']
        
        if not os.path.exists(papers_dir) or len(os.listdir(papers_dir)) == 0:
            logging.error("No research papers found in the papers directory")
            return None

        # Load and process all PDFs in the directory
        documents = []
        for filename in os.listdir(papers_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(papers_dir, filename)
                try:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                except Exception as e:
                    logging.error(f"Error processing {filename}: {e}")

        if not documents:
            logging.error("No documents were successfully loaded")
            return None

        # Split documents into chunks
        texts = self.text_splitter.split_documents(documents)
        
        # Create vector store
        vector_db = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=vector_store_path
        )
        
        return vector_db

    def initialize_resources(self):
        """Initialize the vector database and related resources"""
        vector_store_path = current_app.config['VECTOR_STORE']

        if not os.path.exists(vector_store_path) or len(os.listdir(vector_store_path)) == 0:
            logging.info("Vector store not found or is empty. Processing research papers...")
            self.vector_db = self.process_papers()
            if self.vector_db is None:
                logging.error("Failed to process research papers and create vector store.")
                return
        else:
            logging.info("Loading existing vector store...")
            self.vector_db = Chroma(
                persist_directory=vector_store_path,
                embedding_function=self.embeddings
            )

        # Create retriever and chain
        logging.info("Creating retriever and chain...")
        self.retriever = self.vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=memory,
            verbose=True
        )

        logging.info("Vector database, retriever, and chain initialized successfully.")

    def stream(self, conversation, use_rag=False):
        """Streams the response from the chain or LLM directly, based on use_rag flag."""
        if use_rag:
            if not self.vector_db or not self.chain:
                self.initialize_resources()

            if not self.chain:
                logging.error("Chain is not initialized. Ensure vector DB is loaded correctly.")
                yield "Error: Chain is not initialized.\n".encode('utf-8')
                return

            # Generate response using the RAG chain
            logging.info("Using RAG to generate the response...")
            result = self.chain({"question": conversation[-1]["content"]})
            yield result["answer"].encode('utf-8')
        else:
            # Generate response using the LLM directly
            logging.info("Using LLM directly to generate the response...")
            result = self.llm.invoke(conversation[-1]["content"])
            yield result.content.encode('utf-8')
