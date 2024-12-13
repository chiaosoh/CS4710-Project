import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3 import PPO

# Defining the env for the model to train in
class WorldsHardestGameEnv(gym.Env):
    def __init__(self, grid_size=10, num_dots=5, max_walls=10, max_steps=10000):
        super(WorldsHardestGameEnv, self).__init__()
        
        # Game grid size (nxn)
        self.grid_size = grid_size
        self.num_dots = num_dots
        self.max_walls = max_walls

        # Walls
        self.walls = self.default_level_walls()
        
        # Action space, 8 directions + stay
        self.action_space = spaces.Discrete(9)
        
        self.observation_space = spaces.Box(
            low=0,
            high=self.grid_size - 1,
            shape=(1 + len(self.walls) + self.num_dots + 1, 4),  # player + walls + dots + goal
            dtype=np.float64
        )

        # Limit to encourage moving towards goal
        self.max_steps = max_steps
        self.current_step = 0
        
        self.reset()
    
    def reset(self):
        # Reset step counter
        self.current_step = 0

        # Cube starts at center
        self.cube_position = np.array([self.grid_size // 2, self.grid_size // 2], dtype=np.float64)
        
        # Randomly place 3 dots (they will move randomly)
        self.dots = np.array([[random.randint(0, self.grid_size-1), random.randint(0, self.grid_size-1)] for _ in range(self.num_dots)], dtype=np.float64)
        
        # Randomly place the goal
        self.goal_position = self.place_goal()

        self.walls = self.default_level_walls()
        
        return self.get_observation()
    
    def default_level_walls(self):
        # Walls are defined as [x, y, width, height]
        walls = [
            [0, 0, 0, 9],  # Left wall
            [9, 0, 0, 9],  # Right wall
            [0, 0, 9, 0],  # Top wall
            [0, 9, 9, 0],  # Bottom wall
            [1, 1, 0, 7],  # Vertical wall
            [1, 1, 4, 0],  # Horizontal wall
            [5, 1, 0, 5],  # Horizontal wall
            [2, 3, 0, 4],  # Vertical wall
            [7, 2, 0, 6],  # Vertical wall
            [3, 6, 5, 0]   # Horizontal wall
        ]
        return np.array(walls, dtype=np.float64)
    
    def place_goal(self):
        while True:
            goal = np.array([random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)])
            # Check if goal is outside all walls
            if not any(
                wall[0] <= goal[0] <= wall[0] + wall[2] and wall[1] <= goal[1] <= wall[1] + wall[3]
                for wall in self.walls
            ):
                return goal
            
    def check_wall_collision(self, new_position):
        for wall in self.walls:
            x, y, width, height = wall
            x_min, x_max = x, x + width
            y_min, y_max = y, y + height
            if x_min <= new_position[0] <= x_max and y_min <= new_position[1] <= y_max:
                return True
        return False

    def get_observation(self):
        # Pad the cube_position, dots, and goal with zeros to match the walls' shape
        cube_padded = np.pad(self.cube_position.reshape(1, 2), ((0, 0), (0, 2)), mode='constant')
        goal_padded = np.pad(self.goal_position.reshape(1, 2), ((0, 0), (0, 2)), mode='constant')
        
        # Dots need to be padded to have 4 columns (same as walls)
        dots_padded = np.pad(self.dots, ((0, 0), (0, 2)), mode='constant')

        return np.concatenate(
            [
                cube_padded,  # Cube position
                self.walls,                       # Walls 
                dots_padded,                        # Dots positions
                goal_padded  # Goal position
            ],
            axis=0
        )

    def step(self, action):
        self.current_step += 1
        velocity = np.array([0, 0])
        # Tilesize / 15
        player_speed = 50 / 15

        # Define movement based on action
        action_velocities = {
            0: np.array([-1.0, 1.0]),     # Move up-left
            1: np.array([0.0, 1.0]),       # Move up
            2: np.array([1.0, 1.0]),       # Move up-right
            3: np.array([-1.0, 0.0]),      # Move left
            4: np.array([0.0, 0.0]),       # Stay
            5: np.array([1.0, 0.0]),       # Move right
            6: np.array([-1.0, -1.0]),     # Move down-left
            7: np.array([0.0, -1.0]),      # Move down
            8: np.array([1.0, -1.0])       # Move down-right
        }
        
        velocity = action_velocities.get(action, np.array([0.0, 0.0]))
        velocity *= player_speed
        # Proposed new position
        new_position = self.cube_position + velocity

        # Check wall collision
        if not self.check_wall_collision(new_position):
            self.cube_position = new_position

        # Ensure the cube doesn't go out of bounds
        self.cube_position = np.clip(self.cube_position, 0, self.grid_size-1)

        # Move the dots randomly (TODO: set proper movement)
        for i in range(len(self.dots)):
            dot_velocity = np.array([random.choice([-1.0, 0.0, 1.0]), random.choice([-1.0, 0.0, 1.0])])
            new_dot_pos = self.dots[i] + dot_velocity
            # Avoid walls and grid boundaries
            if not self.check_wall_collision(new_dot_pos):
                self.dots[i] = np.clip(new_dot_pos, 0, self.grid_size-1)
        
        """
        Reward Calculations
        """
        done = False

        # Compute distances to dots and goal
        dot_distances = [np.linalg.norm(self.cube_position - dot) for dot in self.dots]
        goal_distance = np.linalg.norm(self.cube_position - self.goal_position)

        # Dot collision check
        min_dot_distance = min(dot_distances)
        # Significant penalty for being very close to a dot
        if min_dot_distance < 1:
            reward = -100
            done = True
        else:
            # Reward exploration and progress
            # Encourage staying away from dots
            dot_penalty = -5 / (min(dot_distances) + 1)
            
            # Encourage moving towards the goal
            goal_approach_reward = -1 * goal_distance
            
            # Time penalty to encourage faster completion
            time_penalty = -1 * (self.current_step / self.max_steps)
            
            # Combine rewards
            reward = goal_approach_reward + dot_penalty + time_penalty
        # Reached goal
        if np.allclose(self.cube_position, self.goal_position, atol=0.5):
            reward = 10000
            done = True
         # Check for max steps
        if self.current_step >= self.max_steps:
            done = True
            reward = -500  # Penalty for not completing in time

        return self.get_observation(), reward, done, {
            'current_step': self.current_step,
            'goal_distance': goal_distance,
            'dot_distances': dot_distances
        }
    
    def check_collision(self, player_pos, dot_pos, player_diameter=1):
        # Distance between player and dot
        distance = np.linalg.norm(player_pos - dot_pos)
        if distance < player_diameter: 
            return True
        return False
    
# Train the model
if __name__ == '__main__':
    env = WorldsHardestGameEnv(grid_size=10, num_dots=5)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=50000)
    model.save("ppo_worlds_hardest_game")