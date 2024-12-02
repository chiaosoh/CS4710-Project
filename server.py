from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from process_game_state import process_game_state

app = Flask(__name__)
CORS(app)

# Disable OPTIONS message every single time the server receives a POST
@app.before_request
def disable_options_logging():
    if request.method == 'OPTIONS':
        logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

@app.route('/game_state', methods=['POST'])
def game_state():
    game_data = request.json
    reward, player_state = process_game_state(game_data)
    print(f"Calculated reward: {reward}")
    return jsonify({"status": "success", "reward": reward})

if __name__ == '__main__':
    app.run(debug=False, threaded=True)