import pyglet
import math
import os
import json
import pyglet.math

# --- USTAWIENIA ---
WIDTH = 1920
HEIGHT = 1040
GRID_SIZE = 100
MAP_FOLDER = "Mapy"
HIGHSCORE_FILE = "wyniki.json"

# --- STANY GRY ---
STATE_MENU = 0
STATE_GAME = 1
STATE_WIN = 2

current_state = STATE_MENU
current_time = 0.0
final_time = 0.0
current_map_name = ""
is_new_record = False

# --- SYSTEM WYNIKÓW ---
highscores = {}


def load_highscores():
    global highscores
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                highscores = json.load(f)
        except:
            highscores = {}
    else:
        highscores = {}


def save_highscores():
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump(highscores, f)
    except Exception as e:
        print(f"Błąd zapisu: {e}")


load_highscores()


# --- KLASA SAMOCHODU ---
class Car:
    def __init__(self, x, y):
        self.width = 60
        self.height = 40
        # Pozycja w świecie gry
        self.x = x
        self.y = y
        self.angle = 0
        self.acceleration = 45
        self.velocity_x = 0
        self.velocity_y = 0
        self.max_speed = 1000
        self.turn_speed = 4
        self.is_falling = False
        # raycast
        self.raycast_angles = [math.pi / 2, math.pi / 4, 0, -math.pi / 4, -math.pi / 2]
        self.ray_lengths = [0] * len(self.raycast_angles)
        self.raycast_max_range = 700

        self.raycast_lines = []
        for _ in range(len(self.raycast_angles)):
            line = pyglet.shapes.Line(0, 0, 0, 0, thickness=2, color=(255, 0, 0))
            line.opacity = 150
            self.raycast_lines.append(line)

        self.car_image = pyglet.shapes.Rectangle(0, 0, self.width, self.height, color=(255, 0, 20))
        self.car_image.anchor_x = self.width // 2
        self.car_image.anchor_y = self.height // 2

    # ZMIANA: Usunięto keys_state, dodano proste flagi logiczne
    def move(self, dt, surface_grip, left=False, right=False, forward=False, backward=False):
        # 1. Fizyka
        speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)

        if speed > 10:
            turn_scale = min(speed / self.max_speed, 1.0)
            if left:
                self.angle += self.turn_speed * turn_scale * dt
            if right:
                self.angle -= self.turn_speed * turn_scale * dt

        self.angle %= (2 * math.pi)

        heading_x = math.cos(self.angle)
        heading_y = math.sin(self.angle)

        dot_prod = self.velocity_x * heading_x + self.velocity_y * heading_y
        vel_fwd_x = dot_prod * heading_x
        vel_fwd_y = dot_prod * heading_y
        vel_lat_x = self.velocity_x - vel_fwd_x
        vel_lat_y = self.velocity_y - vel_fwd_y

        grip_impact = surface_grip ** 3
        slide_retention = 0.999 - (grip_impact * 0.95)
        vel_lat_x *= slide_retention
        vel_lat_y *= slide_retention

        traction = 0.2 + (0.8 * surface_grip)
        current_accel = self.acceleration * traction

        if forward:
            vel_fwd_x += heading_x * current_accel
            vel_fwd_y += heading_y * current_accel
        elif backward:
            vel_fwd_x -= heading_x * current_accel
            vel_fwd_y -= heading_y * current_accel

        drag = 0.985
        vel_fwd_x *= drag
        vel_fwd_y *= drag

        self.velocity_x = vel_fwd_x + vel_lat_x
        self.velocity_y = vel_fwd_y + vel_lat_y

        new_speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
        if new_speed > self.max_speed:
            scale = self.max_speed / new_speed
            self.velocity_x *= scale
            self.velocity_y *= scale

        # 2. Aktualizacja pozycji (ruch w świecie)
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

    def update_raycast(self, game_map):
        step_size = 10

        for i, angle_offset in enumerate(self.raycast_angles):
            ray_angle = self.angle + angle_offset
            ray_dx = math.cos(ray_angle) * step_size
            ray_dy = math.sin(ray_angle) * step_size

            curr_x = self.x
            curr_y = self.y
            dist = 0

            while dist < self.raycast_max_range:
                curr_x += ray_dx
                curr_y += ray_dy
                dist += step_size

                grip = game_map.get_grip(curr_x, curr_y)

                if grip is None or grip == 0:
                    break
            self.ray_lengths[i] = dist

    def draw(self):
        self.car_image.x = self.x
        self.car_image.y = self.y
        self.car_image.rotation = -math.degrees(self.angle)
        self.car_image.draw()

        # raycast lasers
        for i, angle_offset in enumerate(self.raycast_angles):
            ray_angle = self.angle + angle_offset
            dist = self.ray_lengths[i]

            end_x = self.x + math.cos(ray_angle) * dist
            end_y = self.y + math.sin(ray_angle) * dist

            self.raycast_lines[i].x = self.x
            self.raycast_lines[i].y = self.y
            self.raycast_lines[i].x2 = end_x
            self.raycast_lines[i].y2 = end_y

            self.raycast_lines[i].draw()


# --- KLASA MAPY (Optymalizacja Batch) ---
class Map:
    def __init__(self, file_name):
        self.r_positions = []
        self.batch = pyglet.graphics.Batch()  # Optymalizacja rysowania
        self.shapes = []
        self.grid = self.load_map(file_name)

    def load_map(self, file_name):
        path = os.path.join(MAP_FOLDER, file_name)
        grid = []

        if not os.path.exists(path):
            return []

        with open(path, "r") as f:
            lines = f.readlines()
            self.height = len(lines) * GRID_SIZE
            total_rows = len(lines)

            for y_file, line in enumerate(lines):
                row_data = []
                values = line.strip().split()

                # Przeliczenie Y na układ współrzędnych świata
                world_y = (total_rows - 1 - y_file) * GRID_SIZE

                for x_file, value in enumerate(values):
                    world_x = x_file * GRID_SIZE

                    val = 0.0
                    if value == 'r':
                        val = 1.0
                        self.r_positions.append([world_x, world_y])
                    else:
                        try:
                            val = float(value)
                        except:
                            val = 0.0

                    row_data.append(val)

                    # Generowanie grafiki "raz na zawsze" do Batcha
                    if val > 0:
                        if val == 2.0:
                            col = (255, 0, 0)
                        else:
                            intensity = int(val * 255)
                            col = (intensity, intensity, intensity)

                        rect = pyglet.shapes.Rectangle(
                            world_x, world_y, GRID_SIZE, GRID_SIZE,
                            color=col, batch=self.batch
                        )
                        self.shapes.append(rect)

                grid.append(row_data)

        return grid[::-1]

    def get_grip(self, x, y):
        grid_x = int(x // GRID_SIZE)
        grid_y = int(y // GRID_SIZE)

        if 0 <= grid_y < len(self.grid) and 0 <= grid_x < len(self.grid[0]):
            return self.grid[grid_y][grid_x]
        return None

    def draw(self):
        self.batch.draw()


# --- INICJALIZACJA GRY TYLKO PRZY BEZPOŚREDNIM URUCHOMIENIU ---
if __name__ == "__main__":

    # 1. Tworzymy okno i klawisze
    window = pyglet.window.Window(WIDTH, HEIGHT, "WRUM - Time Trial", resizable=False)
    keys = pyglet.window.key.KeyStateHandler()
    window.push_handlers(keys)

    player_car = None
    game_map = None
    available_maps = []
    selected_map_index = 0


    def refresh_map_list():
        global available_maps
        if not os.path.exists(MAP_FOLDER):
            os.makedirs(MAP_FOLDER)
        files = os.listdir(MAP_FOLDER)
        available_maps = [f for f in files if f.endswith('.txt')]
        if not available_maps:
            available_maps = ["Brak map!"]


    refresh_map_list()


    # --- RESET STANU ---
    def reset_game_state():
        global window, keys
        window.view = pyglet.math.Mat4()
        window.remove_handlers(keys)
        keys = pyglet.window.key.KeyStateHandler()
        window.push_handlers(keys)


    def start_game(map_filename):
        global game_map, player_car, current_state, current_time, current_map_name, is_new_record

        reset_game_state()

        try:
            game_map = Map(map_filename)
            current_map_name = map_filename
            is_new_record = False

            if not game_map.r_positions:
                print("Błąd: Brak 'r' na mapie!")
                return

            rx, ry = game_map.r_positions[0]
            start_x = rx + GRID_SIZE // 2
            start_y = ry + GRID_SIZE // 2

            player_car = Car(start_x, start_y)

            current_time = 0.0
            current_state = STATE_GAME

        except Exception as e:
            print(f"Błąd ładowania mapy: {e}")


    # --- PĘTLA GŁÓWNA ---
    def update(dt):
        global current_state, current_time, final_time, is_new_record

        if current_state == STATE_MENU:
            pass

        elif current_state == STATE_GAME:
            if player_car.is_falling:
                if game_map and game_map.r_positions:
                    rx, ry = game_map.r_positions[0]
                    player_car.x = rx + GRID_SIZE // 2
                    player_car.y = ry + GRID_SIZE // 2
                    player_car.velocity_x = 0
                    player_car.velocity_y = 0
                    player_car.angle = 0
                    player_car.is_falling = False
                    current_time = 0.0
            else:
                current_time += dt

                grip = game_map.get_grip(player_car.x, player_car.y)

                if grip is None or grip == 0:
                    player_car.is_falling = True
                elif grip == 2.0:
                    final_time = current_time
                    old_record = highscores.get(current_map_name)

                    if old_record is None or final_time < old_record:
                        highscores[current_map_name] = final_time
                        save_highscores()
                        is_new_record = True
                    else:
                        is_new_record = False

                    current_state = STATE_WIN
                else:
                    phys_grip = 1.0 if grip >= 2.0 else grip

                    is_left = keys[pyglet.window.key.A]
                    is_right = keys[pyglet.window.key.D]
                    is_forward = keys[pyglet.window.key.W]
                    is_backward = keys[pyglet.window.key.S]

                    player_car.move(dt, phys_grip, left=is_left, right=is_right, forward=is_forward,
                                    backward=is_backward)
                    player_car.update_raycast(game_map)
        elif current_state == STATE_WIN:
            pass


    pyglet.clock.schedule_interval(update, 1 / 60)


    # --- RYSOWANIE ---
    @window.event
    def on_draw():
        window.clear()

        window.view = pyglet.math.Mat4()

        if current_state == STATE_MENU:
            pyglet.text.Label("WRUM - WYBIERZ TRASĘ", font_size=40, x=WIDTH // 2, y=HEIGHT - 100,
                              anchor_x='center').draw()
            pyglet.text.Label("Strzałki: Wybór | ENTER: Start | ESC: Wyjście", font_size=16, x=WIDTH // 2, y=50,
                              anchor_x='center').draw()

            for i, m_name in enumerate(available_maps):
                record = highscores.get(m_name)
                record_str = f"{record:.2f}s" if record else "--.--"
                color = (0, 255, 0, 255) if i == selected_map_index else (255, 255, 255, 255)
                text = f"> {m_name} <   Rekord: {record_str}" if i == selected_map_index else f"{m_name}   Rekord: {record_str}"

                pyglet.text.Label(text, font_size=24, color=color, x=WIDTH // 2, y=HEIGHT - 200 - (i * 45),
                                  anchor_x='center').draw()

        elif current_state == STATE_GAME:
            cam_x = -player_car.x + WIDTH // 2
            cam_y = -player_car.y + HEIGHT // 2
            window.view = pyglet.math.Mat4().translate((cam_x, cam_y, 0))

            game_map.draw()
            player_car.draw()

            window.view = pyglet.math.Mat4()
            pyglet.text.Label(f"Czas: {current_time:.2f}", font_size=24, x=20, y=HEIGHT - 40,
                              color=(255, 255, 0, 255)).draw()

        elif current_state == STATE_WIN:
            cam_x = -player_car.x + WIDTH // 2
            cam_y = -player_car.y + HEIGHT // 2
            window.view = pyglet.math.Mat4().translate((cam_x, cam_y, 0))

            game_map.draw()
            player_car.draw()

            window.view = pyglet.math.Mat4()
            pyglet.shapes.Rectangle(0, 0, WIDTH, HEIGHT, color=(0, 0, 0), batch=None).opacity = 200

            header = "NOWY REKORD!" if is_new_record else "UKOŃCZONE!"
            h_color = (255, 215, 0, 255) if is_new_record else (255, 0, 0, 255)

            pyglet.text.Label(header, font_size=80, color=h_color, x=WIDTH // 2, y=HEIGHT // 2 + 80,
                              anchor_x='center').draw()
            pyglet.text.Label(f"Twój czas: {final_time:.2f} s", font_size=50, color=(0, 255, 0, 255), x=WIDTH // 2,
                              y=HEIGHT // 2 - 20, anchor_x='center').draw()
            pyglet.text.Label("Enter - Menu", font_size=30, x=WIDTH // 2, y=HEIGHT // 2 - 150, anchor_x='center').draw()


    # --- STEROWANIE ---
    @window.event
    def on_key_press(symbol, modifiers):
        global current_state, selected_map_index

        if current_state == STATE_MENU:
            if symbol == pyglet.window.key.UP or symbol == pyglet.window.key.W:
                selected_map_index = (selected_map_index - 1) % len(available_maps)
            elif symbol == pyglet.window.key.DOWN or symbol == pyglet.window.key.S:
                selected_map_index = (selected_map_index + 1) % len(available_maps)
            elif symbol == pyglet.window.key.ENTER or symbol == pyglet.window.key.SPACE:
                if available_maps and available_maps[0] != "Brak map!":
                    start_game(available_maps[selected_map_index])
            elif symbol == pyglet.window.key.ESCAPE:
                window.close()

        elif current_state == STATE_GAME:
            if symbol == pyglet.window.key.ESCAPE:
                current_state = STATE_MENU
                refresh_map_list()
                reset_game_state()
                return pyglet.event.EVENT_HANDLED

        elif current_state == STATE_WIN:
            if symbol == pyglet.window.key.ENTER or symbol == pyglet.window.key.SPACE:
                current_state = STATE_MENU
                refresh_map_list()
                reset_game_state()

    pyglet.app.run()