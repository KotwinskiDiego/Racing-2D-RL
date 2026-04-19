import pyglet
import numpy as np
import math
from KeepGoing_raycast import Map, Car
from stable_baselines3 import PPO

# --- USTAWIENIA OKNA ---
WIDTH, HEIGHT = 800, 600
window = pyglet.window.Window(WIDTH, HEIGHT, "Obserwacja AI - KeepGoing", resizable=False)


map_filename = "tor_treningowy1.txt"
game_map = Map(map_filename)


grid_size = 100
rx, ry = game_map.r_positions[0]
start_x = rx + grid_size // 2
start_y = ry + grid_size // 2


car = Car(start_x, start_y)
car.update_raycast(game_map)

print("Ładowanie mózgu kierowcy...")
model = PPO.load("zapisani_kierowcy/checkpoints/kierowca_2026-04-19_14-28_400704_steps.zip")
print("Kierowca gotowy!")



def get_state():
    norm_rays = [ray / car.raycast_max_range for ray in car.ray_lengths]

    raw_grip = game_map.get_grip(car.x, car.y)
    if raw_grip is None: raw_grip = 0.0
    norm_grip = 1.0 if raw_grip >= 1.0 else 0.0

    norm_vel_x = car.velocity_x / car.max_speed
    norm_vel_y = car.velocity_y / car.max_speed

    norm_angle = (car.angle % (2 * math.pi)) / (2 * math.pi)

    return np.array(norm_rays + [norm_grip, norm_vel_x, norm_vel_y, norm_angle], dtype=np.float32)



def reset_car():
    car.x = start_x
    car.y = start_y
    car.angle = 0
    car.velocity_x = 0
    car.velocity_y = 0
    car.update_raycast(game_map)



def update(dt):

    state = get_state()


    action, _states = model.predict(state, deterministic=False)

    # 3. Odczytujemy decyzję
    steer_act = action[0]
    pedal_act = action[1]

    is_l = (steer_act == 1)
    is_r = (steer_act == 2)
    is_f = (pedal_act == 1)
    is_b = (pedal_act == 2)


    grip = game_map.get_grip(car.x, car.y)
    car.move(dt, grip, is_l, is_r, is_f, is_b)
    car.update_raycast(game_map)


    if grip == 0 or grip == 2 or grip is None:
        print("Koniec trasy! Resetuję...")
        reset_car()


pyglet.clock.schedule_interval(update, 1 / 60)



@window.event
def on_draw():
    window.clear()


    cam_x = -car.x + WIDTH // 2
    cam_y = -car.y + HEIGHT // 2
    window.view = pyglet.math.Mat4().translate((cam_x, cam_y, 0))

    game_map.draw()
    car.draw()



pyglet.app.run()