import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3 import PPO

# Defining the env for the model to train in
class WorldsHardestGameEnv(gym.Env):
    def __init__(self, grid_size=10, num_dots=3):
        super(WorldsHardestGameEnv, self).__init__()
        
        # Game grid size (nxn)
        self.grid_size = grid_size
        self.num_dots = num_dots
        
        # Action space, 8 directions + stay
        self.action_space = spaces.Discrete(9)
        
        # Positions of cube + dots
        self.observation_space = spaces.Box(low=0, high=self.grid_size-1, shape=(self.num_dots + 2, 2), dtype=np.int32)
        
        self.reset()
    
    def reset(self):
        # Cube starts at center
        self.cube_position = np.array([self.grid_size // 2, self.grid_size // 2])
        
        # Randomly place 3 dots (they will move randomly)
        self.dots = np.array([[random.randint(0, self.grid_size-1), random.randint(0, self.grid_size-1)] for _ in range(self.num_dots)])
        
        # Randomly place the goal
        self.goal_position = np.array([random.randint(0, self.grid_size-1), random.randint(0, self.grid_size-1)])

        self.previous_distance_to_goal = np.linalg.norm(self.goal_position - self.cube_position)
        
        return self.get_observation()

    def get_observation(self):
        return np.concatenate([self.cube_position.reshape(1, 2), self.dots, self.goal_position.reshape(1, 2)], axis=0)

    def step(self, action):
        velocity = np.array([0, 0])
        # Tilesize / 15
        player_speed = 50 / 15

        if action == 0:  # Move up-left
            velocity = np.array([-1, 1])
        elif action == 1:  # Move up
            velocity = np.array([0, 1])
        elif action == 2:  # Move up-right
            velocity = np.array([1, 1])
        elif action == 3:  # Move left
            velocity = np.array([-1, 0])
        elif action == 5:  # Move right
            velocity = np.array([1, 0])
        elif action == 6:  # Move down-left
            velocity = np.array([-1, -1])
        elif action == 7:  # Move down
            velocity = np.array([0, -1])
        elif action == 8:  # Move down-right
            velocity = np.array([1, -1])
        elif action == 9: # Stay
            velocity = np.array([0, 0])

        velocity = velocity.astype(np.float64)
        velocity *= player_speed
        self.cube_position = self.cube_position.astype(np.float64)
        self.cube_position += velocity

        # Ensure the cube doesn't go out of bounds
        self.cube_position = np.clip(self.cube_position, 0, self.grid_size-1)

        # Move the dots randomly (TODO: set proper movement)
        self.dots += np.array([random.choice([-1, 0, 1]), random.choice([-1, 0, 1])])
        self.dots = np.clip(self.dots, 0, self.grid_size-1)
        
        # # Dot collision check
        done = False
        # for dot in self.dots:
        #     if self.check_collision(self.cube_position, dot, player_diameter=1):
        #         reward = -100  # Negative reward for collision with a dot
        #         done = True
        #         break
        # # Reached goal
        if np.linalg.norm(self.cube_position - self.goal_position) < 10:
            reward = 3000
            done = True
        # Encourage cube to move towards goal
        else:
            current_distance = np.linalg.norm(self.cube_position - self.goal_position)
            reward = (max(0, 1 / (current_distance + 1e-5)) * 100)

        return self.get_observation(), reward, done, {}
    
    def check_collision(self, player_pos, dot_pos, player_diameter=1):
        # Distance between player and dot
        distance = np.linalg.norm(player_pos - dot_pos)
        if distance < player_diameter: 
            return True
        return False
    
# Train the model
if __name__ == '__main__':
    env = WorldsHardestGameEnv(grid_size=1000, num_dots=5)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=100000)
    model.save("ppo_worlds_hardest_game")