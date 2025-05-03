from flask import Flask, request, jsonify
from flask_cors import CORS
from vertex_search import VertexSearchClient
import traceback # Import traceback
from dotenv import load_dotenv # Import load_dotenv
import os # Import os

# Load environment variables from .env file located in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Construct path to .env in parent dir
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)
# More specific CORS configuration:
# Allow requests specifically from your frontend origin
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Initialize the Vertex Search client
print("Initializing VertexSearchClient...") # Log initialization
try:
    vertex_client = VertexSearchClient()
    print("VertexSearchClient initialized successfully.") # Log success
except Exception as e:
    print(f"!!! Error initializing VertexSearchClient: {e}") # Log init error
    traceback.print_exc()
    vertex_client = None # Set to None if init fails

@app.route('/api/search', methods=['POST'])
def search():
    print("\n--- Received request for /api/search ---") # Log request start
    if not vertex_client:
        print("Error: VertexSearchClient not initialized.")
        return jsonify({"error": "Search client failed to initialize"}), 500

    data = request.get_json()
    if not data:
        print("Error: Request body is not JSON or is empty.")
        return jsonify({"error": "Invalid request body, expected JSON"}), 400

    query = data.get('query')
    print(f"Query received: {query}") # Log query

    if not query:
        print("Error: Query parameter is missing.") # Log missing query
        return jsonify({"error": "Query is required"}), 400

    try:
        print("Calling vertex_client.search...") # Log before calling search
        results = vertex_client.search(query)
        print(f"Search successful. Results: {results}") # Log successful results
        return jsonify(results)
    except Exception as e:
        print(f"!!! Error during vertex_client.search: {e}") # Log the exception
        traceback.print_exc() # Print the full traceback to the console
        return jsonify({"error": "An error occurred during search.", "details": str(e)}), 500

# --- Add similar logging to /api/search-and-answer if you use it ---
@app.route('/api/search-and-answer', methods=['POST'])
def search_and_answer():
    print("\n--- Received request for /api/search-and-answer ---")
    if not vertex_client:
        print("Error: VertexSearchClient not initialized.")
        return jsonify({"error": "Search client failed to initialize"}), 500

    data = request.get_json()
    if not data:
        print("Error: Request body is not JSON or is empty.")
        return jsonify({"error": "Invalid request body, expected JSON"}), 400

    query = data.get('query')
    print(f"Query received: {query}")

    if not query:
        print("Error: Query parameter is missing.")
        return jsonify({"error": "Query is required"}), 400

    try:
        print("Calling vertex_client.search_and_answer...")
        results = vertex_client.search_and_answer(query)
        print(f"Search-and-answer successful. Results: {results}")
        return jsonify(results)
    except Exception as e:
        print(f"!!! Error during vertex_client.search_and_answer: {e}")
        traceback.print_exc()
        return jsonify({"error": "An error occurred during search-and-answer.", "details": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    # Changed port from 5000 to 5001 to avoid potential conflict
    app.run(debug=True, port=5001)