import sys
import json
from stable_baselines3 import PPO
import numpy as np

model = PPO.load("ppo_worlds_hardest_game.zip")

def preprocess_state(data):
    player_state = data.get("player", {})
    # player pos
    player_position = np.array(data.get("player", {}).get("position", [0, 0])).reshape(1, 2)
    # dots
    moving_obstacles = data.get("environment", {}).get("moving_obstacles", [])
    max_dots = 5
    dots_representation = np.array([dot['position'] for dot in moving_obstacles]).reshape(-1, 2)
    # If there are fewer than 5 dots, pad with zeros
    if len(dots_representation) < max_dots:
        dots_representation = np.pad(dots_representation, ((0, max_dots - len(dots_representation)), (0, 0)), mode='constant')
    # goal pos
    goal_position = np.array(data.get("environment", {}).get("goal_area", {}).get("position", [0, 0])).reshape(1, 2)
    state_representation = np.vstack([player_position, dots_representation, goal_position])
    return state_representation

def process_game_state(data):
    observation = preprocess_state(data)
    action, _states = model.predict(observation, deterministic=True)
    action = action.item()
    action_map = {
        0: "up-left",    1: "up",       2: "up-right",
        3: "left",       4: "stay",     5: "right",
        6: "down-left",  7: "down",     8: "down-right"
    }
    move = action_map.get(action, "unknown")
    player_position = observation[0]
    goal_position = observation[-1]
    current_distance = np.linalg.norm(player_position - goal_position)
    reward = -current_distance
    if current_distance < 1:
        reward = 3000
    return reward, move

data = sys.argv[1]
data = json.loads(data)
response = process_game_state(data)
print(response)
sys.stdout.flush()

