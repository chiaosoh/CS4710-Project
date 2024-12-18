from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import logging
from process_game_state import process_game_state

app = Flask(__name__)
CORS(app, resources={r"/game_state": {"origins": "http://localhost:8000"}})

# Disable OPTIONS message every single time the server receives a POST
@app.before_request
def disable_options_logging():
    if request.method == 'OPTIONS':
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

@app.route('/game_state', methods=['POST'])
def game_state():
    if request.method == 'OPTIONS':
        # Preflight request handling
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    elif request.method == 'POST':
        game_data = request.json
        move = process_game_state(game_data)
        response = jsonify({"status": "success", "move": move})
        return response

if __name__ == '__main__':
    app.run(debug=False, threaded=True)