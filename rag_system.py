"""
ResearchExpert class for handling RAG queries with citations
"""

from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
import os
from typing import List, Optional

class ResearchExpert:
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.llm = OllamaLLM(model=model_name)
        self.vector_store = None
        self.qa_chain = None
        self.conversation_history = []
        
        # Define a more specific prompt template with citation requirements
        self.prompt_template = """
CRITICAL RULES:
1. ALWAYS check paper abstracts first for definitions and key concepts within the provided Context.
2. ONLY state what is EXPLICITLY mentioned in the Context (the provided research paper excerpts) - no exceptions and no inferences from outside the Context.
3. DO NOT make ANY assumptions, inferences, or speculations - even if they seem obvious. Stick strictly to the Context.
4. If asked what something stands for or means, ONLY provide the definition if it's EXPLICITLY stated in the Context with phrases like "X stands for Y" or "X is defined as Y".
5. DO NOT define or expand ANY terms or acronyms unless the Context explicitly does so.
6. If information is not directly stated in the Context, respond with "The provided context does not explicitly state [specific detail asked about]."
7. Use exact terminology from the Context - never substitute or rephrase terms.
8. NEVER use hedging language like "likely", "may", "probably", "could have", etc.
9. NEVER speculate about authors' motivations or reasoning unless explicitly stated in the Context.
10. If asked about system purposes or definitions, ONLY provide what the Context explicitly states.
11. ONLY provide 3 sentences MAXIMUM in your response.
12. ONLY use definitions from the Context, never make up your own.
13. When asked "according to the research papers" or similar phrases, ONLY use terminology, definitions, and explanations EXACTLY as they appear in the Context - no external knowledge allowed.
14. When asked about a term or concept, ALWAYS check the abstract sections within the Context first before saying it's not defined.
15. You MUST end your response by citing the specific source document and page number from the Context that supports your answer, formatted as: "[Source: file_name.pdf, Page X]". If multiple sources support the answer, cite the most direct one. If no single source directly supports the *entire* answer but pieces come from the context, state "Based on the provided context."
16. If you are stating that information is not available, you do not need to provide a source citation.

Context:
{context}

Question: {question}

Remember: You must ONLY use information from the provided Context documents above. If you're not 100% certain something is explicitly stated in the Context, say "The provided context does not explicitly state this." Follow all CRITICAL RULES.

Response:"""
        
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
            chunk_size=2000,
            chunk_overlap=400,
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
                    "k": 20  # Increased from 8 to get more comprehensive coverage
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
                    "k": 20  # Changed from 15 to 20 for consistency
                }
            ),
            chain_type_kwargs={
                "prompt": prompt,
                "verbose": True  # Help with debugging
            },
            return_source_documents=True
        )