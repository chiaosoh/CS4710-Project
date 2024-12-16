import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3 import PPO

# Defining the env for the model to train in
class WorldsHardestGameEnv(gym.Env):
    """
    Environment definition
    """
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

    """
    Reset function
    """
    def reset(self):
        # Reset step counter
        self.current_step = 0

        # Cube starts at center
        self.cube_position = np.array([self.grid_size // 2, self.grid_size // 2], dtype=np.float64)
        
        # Randomly place 3 dots (they will move randomly)
        self.dots = np.array([[random.randint(0, self.grid_size-1), random.randint(0, self.grid_size-1)] for _ in range(self.num_dots)], dtype=np.float64)
        
        self.walls = self.default_level_walls()

        # Randomly place the goal
        self.goal_position = self.place_goal()
        
        return self.get_observation()
    
    """
    Default walls (currently only wall layout)
    """
    def default_level_walls(self):
        # Walls are defined as [x, y, width, height]
        walls = []
        for _ in range(self.max_walls):
            # Randomly generate x, y position for the top-left corner of the wall
            x = random.randint(0, self.grid_size - 1)
            y = random.randint(0, self.grid_size - 1)

            if random.choice([True, False]): 
                # Width is large, height is small
                width = random.randint(3, 5)  
                height = random.randint(1, 2)  
            else:
                # Height is large, width is small
                width = random.randint(1, 2) 
                height = random.randint(3, 5)

            # Ensure the wall fits within the grid boundaries
            x = min(x, self.grid_size - width)
            y = min(y, self.grid_size - height)

            # Add the wall to the list
            walls.append([x, y, width, height])
        return np.array(walls, dtype=np.float64)
    
    """
    Randomly places the goal (and ensures its not in a wall)
    """
    def place_goal(self):
        while True:
            goal = np.array([random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)])
            # Check if goal is outside all walls
            if not any(
                wall[0] <= goal[0] <= wall[0] + wall[2] and wall[1] <= goal[1] <= wall[1] + wall[3]
                for wall in self.walls
            ):
                return goal
    
    """
    Wall/player collision check
    """
    def check_wall_collision(self, new_position):
        for wall in self.walls:
            x, y, width, height = wall
            x_min, x_max = x, x + width
            y_min, y_max = y, y + height
            if x_min <= new_position[0] <= x_max and y_min <= new_position[1] <= y_max:
                return True
        return False

    """
    Model observation, need to reshape everything to (17, 4) as defined in the observation space
    """
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

    """
    Step with the model, calculate new player position + rewards
    """
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

        # # If no movement has occurred (position does not change), apply a random movement to "escape"
        # if not np.array_equal(self.cube_position, new_position):
        #     random_action = random.choice([0, 1, 2, 3, 5, 6, 7, 8])  # Randomly choose a new direction
        #     random_velocity = action_velocities[random_action] * player_speed
        #     self.cube_position += random_velocity
        #     self.cube_position = np.clip(self.cube_position, 0, self.grid_size-1)

        # Ensure the cube doesn't go out of bounds
        self.cube_position = np.clip(self.cube_position, 0, self.grid_size-1)

        # Move the dots randomly (TODO: set proper movement)
        for i in range(len(self.dots)):
            dot_velocity = np.array([random.choice([-1.0, 0.0, 1.0]), random.choice([-1.0, 0.0, 1.0])])
            new_dot_pos = self.dots[i] + dot_velocity
            # Avoid walls and grid boundaries
            if not self.check_wall_collision(new_dot_pos):
                self.dots[i] = np.clip(new_dot_pos, 0, self.grid_size-1)
        
        # ------------------------------------------------
        # Reward calculations
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
            dot_penalty = 0
            if min_dot_distance < 50:
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
    env = WorldsHardestGameEnv(grid_size=20, num_dots=5)
    model = PPO("MlpPolicy", env, verbose=1, batch_size=256, n_steps=2048, ent_coef=0.01, learning_rate=1e-4, max_grad_norm=0.5)
    model.learn(total_timesteps=250000)
    model.save("ppo_worlds_hardest_game_2")