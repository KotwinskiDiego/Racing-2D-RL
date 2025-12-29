import pyglet
from pyglet.window import mouse, key
import os

# --- Konfiguracje ---
CELL_SIZE = 20
MAP_FOLDER = "Mapy"

# Upewnij się, że folder istnieje
os.makedirs(MAP_FOLDER, exist_ok=True)


class MapEditor:
    def __init__(self, width, height, file_name, load_existing=False):
        self.width = width
        self.height = height
        self.file_name = file_name

        # Inicjalizacja pustej siatki
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.respawn_point = None

        self.current_grip = 1
        self.batch = pyglet.graphics.Batch()
        self.cell_shapes = [[None for _ in range(width)] for _ in range(height)]
        self.mouse_grid_pos = (0, 0)

        # Jeśli edytujemy istniejącą mapę, wczytaj ją
        if load_existing:
            self.load_map_from_file()

        # Wygeneruj grafikę
        self.create_cells()

    def create_cells(self):
        for y in range(self.height):
            for x in range(self.width):
                self.update_cell_visual(x, y)

    def update_cell_visual(self, x, y):
        val = self.grid[y][x]

        # Kolory
        if val == 0:
            color = (0, 0, 0)  # Czarny
        elif val == 2:
            color = (255, 0, 0)  # Meta
        else:
            intensity = int(val * 255)
            color = (intensity, intensity, intensity)

        # Respawn overwrite
        if self.respawn_point == (x, y):
            color = (0, 255, 0)

        if self.cell_shapes[y][x] is None:
            rect = pyglet.shapes.Rectangle(
                x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=color, batch=self.batch
            )
            self.cell_shapes[y][x] = rect
        else:
            self.cell_shapes[y][x].color = color

    def load_map_from_file(self):
        full_path = os.path.join(MAP_FOLDER, self.file_name)
        if not os.path.exists(full_path):
            print("BŁĄD: Plik nie istnieje! Tworzę pustą mapę.")
            return

        print(f"Wczytywanie mapy: {self.file_name}...")
        try:
            with open(full_path, "r") as f:
                lines = f.readlines()
                # Plik czytamy od góry (linia 0), ale w Pyglet Y=0 jest na dole.
                # Musimy to odwrócić przy wczytywaniu, żeby pasowało do widoku.
                # lines[0] -> to jest góra mapy (Y = height - 1)

                file_height = len(lines)

                # Dostosuj wymiary jeśli mapa z pliku jest inna
                if file_height > 0:
                    self.height = file_height
                    self.width = len(lines[0].split())
                    # Reset siatki do nowych wymiarów
                    self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
                    self.cell_shapes = [[None for _ in range(self.width)] for _ in range(self.height)]

                for i, line in enumerate(lines):
                    # i = 0 to góra pliku -> y = self.height - 1
                    y = self.height - 1 - i

                    values = line.split()
                    for x, val in enumerate(values):
                        if x < self.width and y >= 0:
                            if val == 'r':
                                self.respawn_point = (x, y)
                                self.grid[y][x] = 1.0  # Pod spodem asfalt
                            else:
                                self.grid[y][x] = float(val)
            print("Mapa wczytana pomyślnie!")
        except Exception as e:
            print(f"Błąd wczytywania: {e}")

    def save_map(self):
        full_path = os.path.join(MAP_FOLDER, self.file_name)

        if self.respawn_point is None:
            print("BŁĄD: Nie ustawiono punktu startu (R)!")
            return

        print(f"Zapisywanie do: {full_path}...")
        with open(full_path, "w") as f:
            # NAPRAWA LUSTRZANEGO ODBICIA:
            # Iterujemy od góry (height-1) do dołu (0),
            # żeby linijka nr 1 w pliku odpowiadała górze ekranu.
            for y in range(self.height - 1, -1, -1):
                row_data = []
                for x in range(self.width):
                    if (x, y) == self.respawn_point:
                        row_data.append("r")
                    else:
                        # Formatowanie, żeby usunąć .0 tam gdzie nie trzeba (estetyka pliku)
                        val = self.grid[y][x]
                        if val == int(val):
                            row_data.append(str(int(val)))
                        else:
                            row_data.append(str(val))
                f.write(" ".join(row_data) + "\n")
        print("ZAPISANO!")

    def set_cell(self, x, y, val):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = val
            if self.respawn_point == (x, y):
                self.respawn_point = None
            self.update_cell_visual(x, y)

    def set_respawn(self):
        x, y = self.mouse_grid_pos
        if 0 <= x < self.width and 0 <= y < self.height:
            self.respawn_point = (x, y)
            self.grid[y][x] = 1
            # Odśwież widok
            self.update_cell_visual(x, y)
            print(f"Start ustawiony na: {x}, {y}")


# --- MENU STARTOWE (W KONSOLI) ---
def startup_menu():
    print("\n--- EDYTOR MAP WRUM ---")
    print("1. Nowa Mapa")
    print("2. Edytuj Istniejącą Mapę")

    choice = input("Wybierz opcję (1 lub 2): ")

    filename = ""
    load_mode = False

    if choice == "2":
        files = [f for f in os.listdir(MAP_FOLDER) if f.endswith(".txt")]
        if not files:
            print("Brak map w folderze! Tworzę nową.")
            choice = "1"
        else:
            print("\nDostępne mapy:")
            for i, f in enumerate(files):
                print(f"{i + 1}. {f}")
            try:
                idx = int(input("Wybierz numer mapy: ")) - 1
                if 0 <= idx < len(files):
                    filename = files[idx]
                    load_mode = True
                else:
                    print("Błędny numer. Tworzę nową mapę.")
                    filename = input("Podaj nazwę nowej mapy (np. tor1.txt): ")
            except:
                print("Błąd. Tworzę nową mapę.")
                filename = input("Podaj nazwę nowej mapy (np. tor1.txt): ")

    if choice != "2" or not load_mode:
        filename = input("Podaj nazwę nowej mapy (np. tor1.txt): ")
        if not filename.endswith(".txt"):
            filename += ".txt"

    return filename, load_mode


# --- Uruchomienie ---
selected_filename, is_loading = startup_menu()

# Domyślny rozmiar siatki (60x40 przy kafelku 20px = 1200x800px)
# Jeśli wczytujesz mapę, wymiary same się dostosują w __init__
window = pyglet.window.Window(1200, 800, f"Edytor: {selected_filename}")
editor = MapEditor(60, 40, selected_filename, load_existing=is_loading)


@window.event
def on_draw():
    window.clear()
    editor.batch.draw()

    mx, my = editor.mouse_grid_pos
    rect = pyglet.shapes.Rectangle(mx * CELL_SIZE, my * CELL_SIZE, CELL_SIZE, CELL_SIZE, color=(255, 255, 0),
                                   batch=None)
    rect.opacity = 100
    rect.draw()


@window.event
def on_mouse_motion(x, y, dx, dy):
    editor.mouse_grid_pos = (x // CELL_SIZE, y // CELL_SIZE)


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    editor.mouse_grid_pos = (x // CELL_SIZE, y // CELL_SIZE)
    if buttons & mouse.LEFT:
        gx, gy = editor.mouse_grid_pos
        editor.set_cell(gx, gy, editor.current_grip)


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == mouse.LEFT:
        gx, gy = x // CELL_SIZE, y // CELL_SIZE
        editor.set_cell(gx, gy, editor.current_grip)


@window.event
def on_key_press(symbol, modifiers):
    if symbol == key._1:
        editor.current_grip = 1
    elif symbol == key._2:
        editor.current_grip = 0.2
    elif symbol == key._3:
        editor.current_grip = 0.3
    elif symbol == key._4:
        editor.current_grip = 0.4
    elif symbol == key._5:
        editor.current_grip = 0.5
    elif symbol == key._6:
        editor.current_grip = 0.6
    elif symbol == key._7:
        editor.current_grip = 0.7
    elif symbol == key._8:
        editor.current_grip = 0.8
    elif symbol == key._9:
        editor.current_grip = 0.9
    elif symbol == key._0:
        editor.current_grip = 0

    elif symbol == key.F:
        editor.current_grip = 2


    elif symbol == key.S and (modifiers & key.MOD_CTRL):
        editor.save_map()

    elif symbol == key.DOWN or symbol == key.R:
        editor.set_respawn()


pyglet.app.run()