from rag_system import ResearchExpert
import os
import sys

def main():
    # Initialize the research expert
    expert = ResearchExpert()
    
    # Get the list of research papers
    papers_dir = "instance/research_papers"
    paper_paths = [os.path.join(papers_dir, f) for f in os.listdir(papers_dir) 
                  if f.endswith('.pdf')]
    
    if not paper_paths:
        print("No PDF files found in the research_papers directory.")
        return
    
    print(f"Found {len(paper_paths)} research papers.")
    
    # Load the papers
    print("Loading papers...")
    expert.load_papers(paper_paths)
    
    # Save the vector store
    expert.save_vector_store()
    
    # Get question from command line argument or prompt
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("\nAsk a question about the research papers: ")
            
    try:
        print(f"\nQuestion: {question}\n")
        answer = expert.query(question)
        print("Answer:")
        print("-" * 80)
        if isinstance(answer, dict):
            print(answer['text'])
            if answer.get('evidence'):
                print("\nEvidence:")
                for evidence in answer['evidence']:
                    print(f"- {evidence}")
        else:
            print(answer)
        print("-" * 80)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 