from KeepGoing_raycast import Map,Car
import math
import random
MAP_FOLDER = "Mapy"
class CarEnv:
    def __init__(self, map_filename):
        self.map = Map(map_filename)
        self.grid_size = 100
        rx, ry = self.map.r_positions[0]
        self.start_x = rx + self.grid_size // 2
        self.start_y = ry + self.grid_size // 2
        self.car = Car(self.start_x, self.start_y)
        self.current_step = 0
        self.dt = 1/60

    def get_state(self):
        #can be used only after update_raycast (and move in most cases)
        return self.car.ray_lengths

    def reset(self):
        self.car.x = self.start_x
        self.car.y = self.start_y
        self.car.angle = 0
        self.car.velocity_x = 0
        self.car.velocity_y = 0
        self.car.update_raycast(self.map)
        self.get_state()

    def step(self, action):
        dt = self.dt
        grip = self.map.get_grip(self.car.x, self.car.y)

        steer_act = action[0]
        pedal_act = action[1]

        #if 0 nothing is chosen
        is_l = (steer_act == 1)
        is_r = (steer_act == 2)

        #if 0 nothing is chosen
        is_f = (pedal_act == 1)
        is_b = (pedal_act == 2)

        self.car.move(dt,grip,is_l,is_r,is_f,is_b)
        self.car.update_raycast(self.map)

        done = False
        reward = 0
        if grip == 0:
            done = True
            reward = -100
        if grip == 2:
            done = True
            reward = 1000
        return self.get_state(), reward, done

env = CarEnv("tor1.txt")

state = env.reset()

while True:
    # Na razie losowe akcje (0, 1 lub 2), żeby zobaczyć czy działa fizyka
    action = [random.randint(0, 2) for _ in range(2)]

    next_state, reward, done = env.step(action)
    print(f"x: {env.car.x}, y: {env.car.y}")
    if done:
        state = env.reset()
        print("=========================\nreset\n==============================")