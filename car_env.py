from KeepGoing_raycast import Map, Car
import gymnasium as gym
import numpy as np
import math


MAP_FOLDER = "Mapy"


class CarEnv(gym.Env):
    def __init__(self, map_filename):
        self.map = Map(map_filename)
        self.grid_size = 100
        rx, ry = self.map.r_positions[0]
        self.start_x = rx + self.grid_size // 2
        self.start_y = ry + self.grid_size // 2
        self.car = Car(self.start_x, self.start_y)
        self.current_step = 0
        self.max_steps = 2000
        self.dt = 1 / 60

        self.action_space = gym.spaces.MultiDiscrete([3, 3])

        # Mamy 9 wartości: 5x raycast, 1x grip, 1x vel_x, 1x vel_y, 1x angle
        self.observation_space = gym.spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(9,),
            dtype=np.float32
        )

    def get_state(self):
        # 1. Normalizacja czujników raycast (zasięg do 700) -> wynik od 0.0 do 1.0
        norm_rays = [ray / self.car.raycast_max_range for ray in self.car.ray_lengths]

        raw_grip = self.map.get_grip(self.car.x, self.car.y)
        if raw_grip is None: raw_grip = 0.0

        norm_grip = 1.0 if raw_grip >= 1.0 else raw_grip


        # 3. Normalizacja prędkości (od -1000 do 1000) -> wynik od -1.0 do 1.0
        norm_vel_x = self.car.velocity_x / self.car.max_speed
        norm_vel_y = self.car.velocity_y / self.car.max_speed

        # 4. Normalizacja kąta obrócenia auta (od 0 do 2*PI) -> wynik od 0.0 do 1.0
        norm_angle = (self.car.angle % (2 * math.pi)) / (2 * math.pi)

        # Złożenie wszystkiego w jedną listę (5 + 1 + 1 + 1 + 1 = 9 elementów)
        state = norm_rays + [norm_grip, norm_vel_x, norm_vel_y, norm_angle]
        return state

    def reset(self, seed=None, options=None):
        self.car.x = self.start_x
        self.car.y = self.start_y
        self.car.angle = 0
        self.car.velocity_x = 0
        self.car.velocity_y = 0
        self.current_step = 0
        self.car.update_raycast(self.map)

        return np.array(self.get_state(), dtype=np.float32), {}

    def step(self, action):
        self.current_step += 1
        dt = self.dt
        grip = self.map.get_grip(self.car.x, self.car.y)
        if grip is None:
            grip = 0.0
        steer_act = action[0]
        pedal_act = action[1]

        is_l = (steer_act == 1)
        is_r = (steer_act == 2)
        is_f = (pedal_act == 1)
        is_b = (pedal_act == 2)

        self.car.move(dt, grip, is_l, is_r, is_f, is_b)
        self.car.update_raycast(self.map)

        new_grip = self.map.get_grip(self.car.x, self.car.y)
        done = False
        truncated = False

        if is_f == False:
            reward = -2
        else:
            reward = 1

        info = {}
        if new_grip == 0 or new_grip is None:
            done = True
            reward = -100
        if new_grip == 2:
            done = True
            reward = 10000
            info["lap_time"] = self.current_step * self.dt

        if self.current_step >= self.max_steps:
            truncated = True
        return np.array(self.get_state(), dtype=np.float32), reward, done, truncated, info


