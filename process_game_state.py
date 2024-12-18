import sys
import json
from stable_baselines3 import PPO
import numpy as np

model = PPO.load("ppo_worlds_hardest_game.zip")

"""
Collects and modifies + reshapes the data to pass to the model
Model environment expects a shape of (17, 4)
"""
def preprocess_state(data):
    """
    
    """
    # Player pos
    player_position = np.array(data.get("player", {}).get("position", [0, 0]) + [0, 0]).reshape(1, 4)
    # Walls (solids)
    walls = data.get("environment", {}).get("walls", [])
    walls_representation = np.array([
        wall['position'] + [abs(wall['size'][0]), abs(wall['size'][1])]
        for wall in walls
    ]).reshape(-1, 4)
    # Dots
    moving_obstacles = data.get("environment", {}).get("moving_obstacles", [])
    dots_representation = np.array([
        dot['position'] + dot['velocity'] + [dot['size']] for dot in moving_obstacles
    ]).reshape(-1, 4)
    # Goal pos
    goal_position = np.array(data.get("environment", {}).get("goal_area", {}).get("position", [0, 0]) + [0, 0]).reshape(1, 4)

    max_walls = 10
    max_dots = 5
    # Pad representations to fixed sizes
    if len(walls_representation) < max_walls:
        walls_representation = np.pad(walls_representation, ((0, max_walls - len(walls_representation)), (0, 0)), mode='constant')
    if len(dots_representation) < max_dots:
        dots_representation = np.pad(dots_representation, ((0, max_dots - len(dots_representation)), (0, 0)), mode='constant')

    state_representation = np.vstack([
        player_position, 
        walls_representation, 
        dots_representation, 
        goal_position
    ])
    return state_representation

"""
Sends the data for preprocessing, feeds it to the model, returns the model's move decision
"""
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
    return move