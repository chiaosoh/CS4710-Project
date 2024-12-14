import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3 import PPO

class WorldsHardestGameEnv(gym.Env):
    def __init__(self, grid_size=100, num_dots=30, max_time_steps=100):
        super(WorldsHardestGameEnv, self).__init__()
        
        # Game grid size (nxn)
        self.grid_size = grid_size
        self.num_dots = num_dots
        self.max_time_steps = max_time_steps
        
        # Action space, 8 directions + stay
        self.action_space = spaces.Discrete(9)
        
        # Positions of cube + dots
        self.observation_space = spaces.Box(low=0, high=self.grid_size-1, shape=(self.num_dots + 2 + 1, 2), dtype=np.float32)
        
        # Dot movement patterns for more predictable challenges
        self.dot_movement_patterns = [
            np.array([1, 0]),   # Horizontal right
            np.array([-1, 0]),  # Horizontal left
            np.array([0, 1]),   # Vertical up
            np.array([0, -1]),  # Vertical down
            np.array([1, 1]),   # Diagonal up-right
            np.array([-1, -1]), # Diagonal down-left
        ]
        
        # Tracking for smarter dot movement
        self.dot_current_pattern_indices = None
        
        self.reset()
    
    def reset(self):
        # Cube starts at center
        self.cube_position = np.array([self.grid_size // 2, self.grid_size // 2], dtype=np.float32)
        
        # Ensure dots are reasonably spread out
        self.dots = self._generate_well_distributed_dots()
        
        # Randomly place the goal, ensuring it's not too close to dots or start
        self.goal_position = self._generate_goal_position()
        
        # Reset dot movement patterns
        self.dot_current_pattern_indices = [
            random.randint(0, len(self.dot_movement_patterns) - 1) 
            for _ in range(self.num_dots)
        ]
        
        self.current_time_step = 0
        return self.get_observation()

    def _generate_well_distributed_dots(self):
        dots = []
        attempts = 0
        while len(dots) < self.num_dots:
            attempts += 1
            if attempts > 100:  # Prevent infinite loop
                raise ValueError("Could not generate well-distributed dots")
            
            candidate = np.array([
                random.randint(0, self.grid_size-1), 
                random.randint(0, self.grid_size-1)
            ], dtype=np.float32)
            
            # Check distance from start position
            start_distance = np.linalg.norm(candidate - np.array([self.grid_size // 2, self.grid_size // 2]))
            
            # Check distance from existing dots
            dot_distances = [np.linalg.norm(candidate - existing) for existing in dots] if dots else []
            
            # Ensure dots are not too close to each other or the start position
            if (start_distance > 2 and 
                (not dot_distances or all(distance > 2 for distance in dot_distances))):
                dots.append(candidate)
        
        return np.array(dots)

    def _generate_goal_position(self):
        attempts = 0
        min_distance_from_player = self.grid_size // 2
        while attempts < 1000:
            goal = np.array([
                random.randint(0, self.grid_size-1), 
                random.randint(0, self.grid_size-1)
            ], dtype=np.float32)
            
            # Ensure goal is not too close to dots or start position
            if (np.linalg.norm(goal - self.cube_position) > min_distance_from_player and 
                all(np.linalg.norm(goal - dot) > 2 for dot in self.dots)):
                return goal
        
            
            attempts += 1
        
        raise ValueError("Could not generate goal position")

    def get_observation(self):
        time_feature = np.array([[self.current_time_step, 0]], dtype=np.float32)
        return np.concatenate([
            self.cube_position.reshape(1, 2), 
            self.dots, 
            self.goal_position.reshape(1, 2), 
            time_feature
        ], axis=0)

    def step(self, action):
        # More precise movement mapping
        movement_map = {
            0: np.array([-1, 1]),    # Move up-left
            1: np.array([0, 1]),      # Move up
            2: np.array([1, 1]),      # Move up-right
            3: np.array([-1, 0]),     # Move left
            4: np.array([0, 0]),      # Stay
            5: np.array([1, 0]),      # Move right
            6: np.array([-1, -1]),    # Move down-left
            7: np.array([0, -1]),     # Move down
            8: np.array([1, -1])      # Move down-right
        }

        velocity = movement_map.get(action, np.array([0, 0]))
        player_speed = 50 / 15

        velocity = velocity.astype(np.float32)
        velocity *= player_speed
        self.cube_position += velocity

        # Ensure the cube doesn't go out of bounds
        self.cube_position = np.clip(self.cube_position, 0, self.grid_size-1)

        # Smarter dot movement using predefined patterns
        for i in range(len(self.dots)):
            pattern_index = self.dot_current_pattern_indices[i]
            movement = self.dot_movement_patterns[pattern_index]
            
            self.dots[i] += movement * (player_speed / 2)
            self.dots[i] = np.clip(self.dots[i], 0, self.grid_size-1)
            
            # Occasionally change dot movement pattern
            if random.random() < 0.1:
                self.dot_current_pattern_indices[i] = random.randint(
                    0, len(self.dot_movement_patterns) - 1
                )
        
        # Dot collision check with more precise collision detection
        done = False
        reward = 0
        for dot in self.dots:
            if self.check_collision(self.cube_position, dot, player_diameter=1.5):
                reward = -200  # Significant penalty for dot collision
                done = True
                break
        
        # Reached goal with more lenient goal detection
        if np.linalg.norm(self.cube_position - self.goal_position) < 1.5:
            reward = 100
            done = True
        else:
            # More nuanced distance-based reward
            distance_to_goal = np.linalg.norm(self.cube_position - self.goal_position)
            reward = -distance_to_goal * 1  # Scaled reward for approach
        
        self.current_time_step += 1
        if self.current_time_step >= self.max_time_steps:
            done = True
            reward -= 100  # Penalty for not reaching goal in time
        
        reward -= 1
        return self.get_observation(), reward, done, {}
    

    def check_collision(self, player_pos, dot_pos, player_diameter=1.5):
        # More precise collision detection
        distance = np.linalg.norm(player_pos - dot_pos)
        return distance < player_diameter
    
    
# Train the model
if __name__ == '__main__':
    env = WorldsHardestGameEnv(grid_size=10, num_dots=5)
    
    # Improved training configuration
    model = PPO(
        "MlpPolicy", 
        env, 
        learning_rate=3e-4,  # Adjusted learning rate
        n_steps=2048,        # Increased number of steps per update
        batch_size=64,       # Appropriate batch size
        n_epochs=10,         # More epochs for better learning
        gamma=0.99,          # Discount factor
        clip_range=0.2,      # Slightly adjusted clip range
        verbose=1
    )

    # Longer training with progress tracking
    model.learn(total_timesteps=100000)
    model.save("ppo_worlds_hardest_game")