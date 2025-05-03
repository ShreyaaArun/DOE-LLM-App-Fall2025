"""
ciobrain/__init__.py

This module initialized the Flask application, sets up configuration settings,
and handles API routes.
"""

import os
from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from rag_system import ResearchExpert
import subprocess
import requests

# Initialize the ResearchExpert
expert = ResearchExpert(model_name="llama3.2")
expert.load_vector_store()  # Load existing vector store

# Define Google Cloud API constants
API_BASE_URL = "https://discoveryengine.googleapis.com/v1alpha/projects/341304510567/locations/global/collections/default_collection/engines/doe-test_1745604392169/servingConfigs/default_search"

def create_app(test_config=None):
    """Initialize and configure the Flask app instance"""

    app = Flask(__name__, instance_relative_config=True)
    
    # Configure CORS with specific settings
    cors = CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],  # Allow both localhost and 127.0.0.1
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
                "max_age": 3600  # Cache preflight requests for 1 hour
            }
        }
    )
    
    # Add CORS headers to all responses
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin in ['http://localhost:5173', 'http://127.0.0.1:5173']:
            response.headers['Access-Control-Allow-Origin'] = origin
        if request.method == 'OPTIONS':
            response.headers.add('Access-Control-Max-Age', '3600')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # Handle OPTIONS requests for all API routes
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        return '', 204

    # Error handler for CORS-related issues
    @app.errorhandler(500)
    def handle_500(e):
        if 'Origin' in request.headers:
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(e)
            }), 500, {
                'Access-Control-Allow-Origin': request.headers.get('Origin'),
                'Access-Control-Allow-Credentials': 'true'
            }
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500

    # Default configuration settings
    app.config.from_mapping(
        SECRET_KEY='dev',  # Set your own in production
        FRONTEND_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # Serve static files from the frontend build directory
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(app.config['FRONTEND_DIR'], path)):
            return send_from_directory(app.config['FRONTEND_DIR'], path)
        else:
            return send_from_directory(app.config['FRONTEND_DIR'], 'index.html')

    # API Routes
    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({'error': 'No message provided'}), 400

            def generate():
                # Get response from RAG system
                response = expert.query(data['message'])
                
                # Get main text and evidence
                main_text = response['text']
                evidence = response.get('evidence', [])
                
                # First send the main text word by word
                words = main_text.split()
                for word in words:
                    yield f"data: {word}\n\n"
                
                # Send evidence as a special JSON message if we have any
                if evidence:
                    import json
                    evidence_json = json.dumps({
                        'type': 'evidence',
                        'data': evidence
                    })
                    yield f"data: {evidence_json}\n\n"
                    
            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Transfer-Encoding': 'chunked'
                }
            )
            
        except Exception as e:
            print(f"Error in /api/chat: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    # Get access token using gcloud CLI or API key
    def get_access_token():
        """Get Google Cloud API key or access token."""
        # First try environment variable
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            print("Using API key from environment variable")
            return api_key

        # Then try gcloud CLI
        try:
            print("Trying to use gcloud CLI...")
            result = subprocess.run(['gcloud', 'auth', 'print-access-token'], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Warning: gcloud CLI error: {e}")
        except FileNotFoundError as e:
            print(f"Warning: gcloud CLI error: {e}")

        # Finally, use hardcoded key (development only)
        print("Using hardcoded API key (for development only)")
        return "YOUR_HARDCODED_API_KEY"  # Replace with your actual API key for development

    # Add these routes to your Flask application
    @app.route('/api/search', methods=['POST'])
    def search():
        data = request.json
        query = data.get('query')
        new_session = data.get('newSession', True)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        try:
            # Get authorization token (API key or access token)
            auth_value = get_access_token()
            print(f"Using authentication value (first 10 chars): {auth_value[:10]}...")
            
            # Set up headers - always use as API key for now
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": auth_value
            }
            
            # Prepare request payload
            session_param = '-' if new_session else data.get('sessionId', '-')
            payload = {
                "query": query,
                "pageSize": 10,
                "queryExpansionSpec": {"condition": "AUTO"},
                "spellCorrectionSpec": {"mode": "AUTO"},
                "languageCode": "en-US",
                "contentSearchSpec": {
                    "extractiveContentSpec": {
                        "maxExtractiveAnswerCount": 1,
                        "maxExtractiveSegmentCount": 1
                    }
                },
                "session": session_param
            }
            
            # Print request details for debugging
            print(f"Making request to: {API_BASE_URL}:search")
            print(f"Headers: {headers}")
            print(f"Payload: {payload}")
            
            # Make the request directly using Python requests
            response = requests.post(
                f"{API_BASE_URL}:search",
                headers=headers,
                json=payload
            )
            
            # Print response details for debugging
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:500]}...")  # Print first 500 chars
            
            # Check for errors
            response.raise_for_status()
            result = response.json()
            
            return jsonify({
                "results": result.get("results", []),
                "sessionInfo": {
                    "queryId": result.get("queryId"),
                    "sessionId": result.get("session")
                }
            })
        
        except requests.exceptions.RequestException as e:
            print(f"Detailed error info: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Error response body: {e.response.text}")
            return jsonify({"error": "Failed to search", "details": str(e)}), 500
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return jsonify({"error": "Failed to search", "details": str(e)}), 500

    @app.route('/api/generate-answer', methods=['POST'])
    def generate_answer():
        data = request.json
        query_id = data.get('queryId')
        session_id = data.get('sessionId')
        
        if not query_id or not session_id:
            return jsonify({"error": "QueryId and SessionId are required"}), 400
        
        try:
            # Get authorization token (API key or access token)
            auth_value = get_access_token()
            
            # Set up headers based on auth type
            headers = {
                "Content-Type": "application/json"
            }
            
            # If it looks like a token, use Bearer auth, otherwise use API key
            if len(auth_value) > 20 and ' ' not in auth_value:
                headers["Authorization"] = f"Bearer {auth_value}"
            else:
                headers["x-goog-api-key"] = auth_value
            
            # Prepare request payload
            payload = {
                "query": {
                    "text": "",
                    "queryId": query_id
                },
                "session": session_id,
                "relatedQuestionsSpec": {"enable": True},
                "answerGenerationSpec": {
                    "ignoreAdversarialQuery": True,
                    "ignoreNonAnswerSeekingQuery": False,
                    "ignoreLowRelevance": False
                }
            }
            
            # Make the request directly using Python requests
            response = requests.post(
                f"{API_BASE_URL}:answer",
                headers=headers,
                json=payload
            )
            
            # Check for errors
            response.raise_for_status()
            result = response.json()
            
            return jsonify({
                "answer": result.get("answer"),
                "relatedQuestions": result.get("relatedQuestions", [])
            })
        
        except Exception as e:
            print(f"Generate Answer API error: {e}")
            return jsonify({"error": "Failed to generate answer", "details": str(e)}), 500

    return app
