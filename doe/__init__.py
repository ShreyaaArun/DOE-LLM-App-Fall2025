"""
doe/__init__.py

This module initialized the Flask application, sets up configuration settings,
and handles API routes.
"""

import os
from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from rag_system import DOEOracle

# Initialize the DOE Oracle
expert = DOEOracle(model_name="CombinatorialExpert")

# Construct absolute paths to the papers
base_dir = os.path.abspath(os.path.dirname(__file__))
paper_paths = [
    os.path.join(base_dir, "..", "instance/research_papers/Applying_Combinatorial_Testing_in_Industrial_Settings.pdf"),
    os.path.join(base_dir, "..", "instance/research_papers/How does combinatorial testing perform in the real world.pdf"),
    os.path.join(base_dir, "..", "instance/research_papers/improving mc&dc and fault detection strength using combinatorial testing.pdf.pdf")
]

# Check if vector store exists, otherwise load papers
vector_store_path = os.path.join(base_dir, "..", "instance/vector_store")
if not os.path.exists(vector_store_path) or not os.listdir(vector_store_path):
    print("Vector store not found, loading papers...")
    expert.load_papers(paper_paths)
    print("Papers loaded and vector store created successfully.")
else:
    print("Loading existing vector store...")
    expert.load_vector_store()  # Load existing vector store
    print("Vector store loaded successfully.")


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
        FRONTEND_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'doe-frontend', 'dist')
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
    @app.route('/api/search', methods=['POST', 'OPTIONS'])
    def search():
        if request.method == 'OPTIONS':
            return '', 204
        
        try:
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400

            # Get response from RAG system
            response = expert.query(data['query'])
            
            # Format response to match frontend expectations
            formatted_results = {
                "summary": response.get("text"),
                "results": response.get("evidence", [])
            }
            
            return jsonify(formatted_results)
            
        except Exception as e:
            print(f"Error in /api/search: {e}")
            return jsonify({'error': 'Internal server error'}), 500

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

    return app
