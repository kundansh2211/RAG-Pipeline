from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import index_service  # Import the service module

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/query_index', methods=['POST'])
def query_index():
    # Get the query from the request
    data = request.json
    query = data.get('query', '')

    # Query the index
    response = index_service.query_index(query)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
