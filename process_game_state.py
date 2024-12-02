import sys
import json

def process_game_state(data):
    player_state = data.get("player", {})
    position = player_state.get("position", [])
    velocity = player_state.get("velocity", [])
    is_dead = player_state.get("is_dead", False)
    reward = sum(position)
    return reward, player_state


if __name__ == "__main__":
    input_data = sys.stdin.read()
    process_game_state(input_data)