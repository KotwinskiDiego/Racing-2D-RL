import pyglet
import numpy as np
import math
import json
import os
from KeepGoing_raycast import Map, Car
from stable_baselines3 import PPO

# --- USTAWIENIA OKNA ---
WIDTH, HEIGHT = 800, 600
window = pyglet.window.Window(WIDTH, HEIGHT, "Obserwacja AI - KeepGoing", resizable=False)

map_filename = "tor1.txt"
game_map = Map(map_filename)

grid_size = 100
rx, ry = game_map.r_positions[0]
start_x = rx + grid_size // 2
start_y = ry + grid_size // 2

car = Car(start_x, start_y)
car.update_raycast(game_map)

print("Ładowanie mózgu kierowcy...")
model = PPO.load("zapisani_kierowcy/checkpoints/kierowca_2026-04-19_20-53_5000704_steps.zip")
print("Kierowca gotowy!")

# ==========================================
# --- SYSTEM WYNIKÓW I TIMER ---
# ==========================================
RESULTS_FILE = "wyniki_AI.json"
lap_timer = 0.0

def load_best_times():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_best_time(track, time):
    records = load_best_times()
    # Zapisz jeśli nie ma jeszcze rekordu na tym torze LUB nowy czas jest lepszy
    if track not in records or time < records[track]:
        records[track] = time
        with open(RESULTS_FILE, "w") as f:
            json.dump(records, f)
        print(f"🏆 NOWY REKORD AI NA {track}! Czas: {time:.3f} s")
        return True
    return False

# Wczytujemy rekordy na start
best_times = load_best_times()
current_best = best_times.get(map_filename, "Brak rekordu")

# Etykiety tekstowe do wyświetlania na ekranie (HUD)
timer_label = pyglet.text.Label(
    'Czas: 0.000 s',
    font_name='Arial', font_size=16,
    x=15, y=HEIGHT - 25, color=(255, 255, 255, 255)
)

record_label = pyglet.text.Label(
    f'Rekord AI: {current_best if isinstance(current_best, str) else f"{current_best:.3f} s"}',
    font_name='Arial', font_size=14,
    x=15, y=HEIGHT - 50, color=(255, 215, 0, 255) # Złoty kolor
)
# ==========================================

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
    global lap_timer
    car.x = start_x
    car.y = start_y
    car.angle = 0
    car.velocity_x = 0
    car.velocity_y = 0
    car.update_raycast(game_map)
    lap_timer = 0.0  # Resetujemy timer przy restarcie auta


def update(dt):
    global lap_timer
    lap_timer += dt  # Bijemy licznik czasu!
    timer_label.text = f'Czas: {lap_timer:.3f} s'

    state = get_state()
    action, _states = model.predict(state, deterministic=False)

    # Odczytujemy decyzję
    steer_act = action[0]
    pedal_act = action[1]

    is_l = (steer_act == 1)
    is_r = (steer_act == 2)
    is_f = (pedal_act == 1)
    is_b = (pedal_act == 2)

    grip = game_map.get_grip(car.x, car.y)
    car.move(dt, grip, is_l, is_r, is_f, is_b)
    car.update_raycast(game_map)

    # Sprawdzanie czy meta czy ściana
    if grip == 0 or grip is None:
        print("Ściana! Resetuję...")
        reset_car()
    elif grip == 2:
        print(f"Meta! Czas okrążenia: {lap_timer:.3f} s")
        # Zapisz wynik jeśli to nowy rekord
        if save_best_time(map_filename, lap_timer):
            # Odśwież też etykietę na ekranie z nowym złotym rekordem
            record_label.text = f'Rekord AI: {lap_timer:.3f} s'
        reset_car()


pyglet.clock.schedule_interval(update, 1 / 60)


@window.event
def on_draw():
    window.clear()

    # Ustawienie kamery podążającej za autem
    cam_x = -car.x + WIDTH // 2
    cam_y = -car.y + HEIGHT // 2
    window.view = pyglet.math.Mat4().translate((cam_x, cam_y, 0))

    # Rysowanie mapy i auta
    game_map.draw()
    car.draw()

    # --- RESET WIDOKU DLA HUD ---
    # To jest kluczowe! Zdejmujemy matrycę translacji kamery, żeby tekst
    # narysował się płasko na ekranie (w lewym górnym rogu), a nie poleciał gdzies z mapą.
    window.view = pyglet.math.Mat4()
    timer_label.draw()
    record_label.draw()


pyglet.app.run()