# WRUM - Time Trial Racing

WRUM is a physics-based, top-down racing game developed in Python using Pyglet. The goal is to set the fastest time on custom grid-based tracks without falling into the void.

## 📦 Installation & Run

1.  **Requirements:** Python 3.6+ and the Pyglet library.
2.  **Install Library:**
    ```bash
    pip install pyglet
    ```
3.  **Start Game:**
    ```bash
    python WRUM.py
    ```

---

## 🎮 Game Controls

| Key | Action |
| :--- | :--- |
| **W** | Accelerate |
| **S** | Brake / Reverse |
| **A / D** | Turn Left / Right |
| **ENTER** | Select Map / Restart Game |
| **ESC** | Main Menu / Exit |

---

## 🛠️ Map Editor (Recommended Way)

The game includes a visual Map Editor to make track building easy.

1.  **Launch the Editor:**
    ```bash
    python map_editor.py
    ```
2.  **Usage:** Select a tool with the keyboard and draw with your mouse.
3.  **Saving:** Press **Ctrl+S** 

### Map Editor Controls

| Input          | Action                                                         |
|:---------------|:---------------------------------------------------------------|
| **Left Click** | Place Block (Draw)                                             | 
| **Key '0'**    | Erase Block (Void)                                             |
| **Key '1'**    | Select **Road** (Full friction)                                |
| **Key '2-9'**  | Select **Slippery Road** (2 = Low friction, 9 = High friction) |
| **Key 'F'**    | Select **Finish Line** |
| **Key 'R'**    | Select **Start Position** |
| **Ctrl + S**   | **Save Map** |

---

## 📝 Manual Map Creation (Text File Method)

Alternatively, you can create maps using a simple text editor (like Notepad).

1. Go to the `Mapy/` folder.
2. Create a new text file (e.g., `my_track.txt`).
3. Type the characters below to build your track using the legend below.

### Text Legend

| Character | Result in Game |
| :---: | :--- |
| **`r`** | **Start Position** (Required) |
| **`1`** | **Road** (Standard Grip) |
| **`2`** | **Finish Line** |
| **`0`** | **Void** (Empty space) |
| **`0.1`** | **Ice** (Low Grip) |
| **`0.5`** | **Dirt** (Medium Grip) |

### Example Layout
```text
0 0 0 0 0
0 1 1 1 0
r 1 0 2 0
0 1 1 1 0
0 0 0 0 0