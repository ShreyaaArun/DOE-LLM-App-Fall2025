from flask import Flask, request, jsonify
from flask_cors import CORS
from vertex_search import VertexSearchClient
import traceback
from dotenv import load_dotenv
import os

# Load environment variables from .env in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)

# CORS configuration to allow localhost and production frontend
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5174", "https://doe-oracle.web.app"]}})

# Initialize VertexSearchClient
print("Initializing VertexSearchClient...")
try:
    vertex_client = VertexSearchClient()
    print("VertexSearchClient initialized successfully.")
except Exception as e:
    print(f"!!! Error initializing VertexSearchClient: {e}")
    traceback.print_exc()
    vertex_client = None

@app.route('/api/search', methods=['POST', 'OPTIONS'])
def search():
    if request.method == 'OPTIONS':
        return '', 204

    print("\n--- Received request for /api/search ---")
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
        print("Calling vertex_client.search...")
        results = vertex_client.search(query)
        print(f"Search successful. Results: {results}")
        return jsonify(results)
    except Exception as e:
        print(f"!!! Error during vertex_client.search: {e}")
        traceback.print_exc()
        return jsonify({"error": "An error occurred during search.", "details": str(e)}), 500

@app.route('/api/search-and-answer', methods=['POST', 'OPTIONS'])
def search_and_answer():
    if request.method == 'OPTIONS':
        return '', 204

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
