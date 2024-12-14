import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

class WorldsHardestGameEnv(gym.Env):
    def __init__(self, grid_size=10, num_dots=3, max_time_steps=100):
        super(WorldsHardestGameEnv, self).__init__()
        self.grid_size = grid_size
        self.num_dots = num_dots
        self.max_time_steps = max_time_steps
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Box(low=0, high=self.grid_size-1, shape=(self.num_dots + 2 + 1, 2), dtype=np.float32)
        self.dot_movement_patterns = [
            np.array([1, 0]), np.array([-1, 0]), np.array([0, 1]), np.array([0, -1]),
            np.array([1, 1]), np.array([-1, -1]), np.array([1, -1]), np.array([-1, 1])
        ]
        self.dot_current_pattern_indices = None
        self.reset()

    def reset(self):
        self.cube_position = np.array([self.grid_size // 2, self.grid_size // 2], dtype=np.float32)
        self.dots = self._generate_well_distributed_dots()
        self.goal_position = self._generate_goal_position()
        self.dot_current_pattern_indices = [random.randint(0, len(self.dot_movement_patterns) - 1) for _ in range(self.num_dots)]
        self.current_time_step = 0
        self.initial_distance_to_goal = np.linalg.norm(self.cube_position - self.goal_position)
        return self.get_observation()

    def _generate_well_distributed_dots(self):
        dots = []
        min_distance = self.grid_size * 0.05
        while len(dots) < self.num_dots:
            candidate = np.array([random.uniform(0, self.grid_size-1), random.uniform(0, self.grid_size-1)], dtype=np.float32)
            if all(np.linalg.norm(candidate - dot) > min_distance for dot in dots):
                dots.append(candidate)
        return np.array(dots)

    def _generate_goal_position(self):
        min_distance = self.grid_size * 0.3
        while True:
            goal = np.array([random.uniform(0, self.grid_size-1), random.uniform(0, self.grid_size-1)], dtype=np.float32)
            if np.linalg.norm(goal - self.cube_position) > min_distance:
                return goal

    def get_observation(self):
        time_feature = np.array([[self.current_time_step / self.max_time_steps, 0]], dtype=np.float32)
        return np.concatenate([
            self.cube_position.reshape(1, 2) / self.grid_size,
            self.dots / self.grid_size,
            self.goal_position.reshape(1, 2) / self.grid_size,
            time_feature
        ], axis=0)

    def step(self, action):
        movement_map = {
            0: np.array([-1, 1]), 1: np.array([0, 1]), 2: np.array([1, 1]),
            3: np.array([-1, 0]), 4: np.array([0, 0]), 5: np.array([1, 0]),
            6: np.array([-1, -1]), 7: np.array([0, -1]), 8: np.array([1, -1])
        }
        velocity = movement_map.get(action, np.array([0, 0]))
        player_speed = self.grid_size * 0.02
        velocity = velocity.astype(np.float32) * player_speed
        self.cube_position += velocity
        self.cube_position = np.clip(self.cube_position, 0, self.grid_size-1)

        for i in range(len(self.dots)):
            pattern_index = self.dot_current_pattern_indices[i]
            movement = self.dot_movement_patterns[pattern_index]
            self.dots[i] += movement * (player_speed * 0.5)
            self.dots[i] = np.clip(self.dots[i], 0, self.grid_size-1)
            if random.random() < 0.05:
                self.dot_current_pattern_indices[i] = random.randint(0, len(self.dot_movement_patterns) - 1)

        done = False
        reward = 0

        # Collision check
        player_radius = 1.5
        for dot in self.dots:
            if np.linalg.norm(self.cube_position - dot) < player_radius:
                reward = -1
                done = True
                break

        # Goal check
        distance_to_goal = np.linalg.norm(self.cube_position - self.goal_position)
        if distance_to_goal < player_radius:
            reward = 1
            done = True
        else:
            # Progress reward
            progress = (self.initial_distance_to_goal - distance_to_goal) / self.initial_distance_to_goal
            reward = progress * 0.01

        self.current_time_step += 1
        if self.current_time_step >= self.max_time_steps:
            done = True

        return self.get_observation(), reward, done, {}

if __name__ == '__main__':
    env = WorldsHardestGameEnv(grid_size=10, num_dots=3)
    model = PPO("MlpPolicy", env, learning_rate=3e-4, n_steps=2048, batch_size=64, n_epochs=10, gamma=0.99, clip_range=0.2, verbose=1)

    total_timesteps = 0
    max_total_timesteps = 10_000_000

    while total_timesteps < max_total_timesteps:
        model.learn(total_timesteps=100_000)
        total_timesteps += 100_000

        eval_env = WorldsHardestGameEnv(grid_size=10, num_dots=3)
        mean_reward, std_reward = evaluate_policy(model, eval_env, n_eval_episodes=10)
        print(f"Total Timesteps: {total_timesteps}")
        print(f"Mean Reward: {mean_reward:.2f} ± {std_reward:.2f}")

        model.save(f"ppo_worlds_hardest_game_checkpoint")

        if mean_reward > 0.5:
            print("Target reward achieved!")
            break

    model.save("ppo_worlds_hardest_game_final")
