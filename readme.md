# WRUM - AI Time Trial Racing

WRUM is a physics-based, top-down racing environment developed in Python using Pyglet. In this project, an AI agent uses Reinforcement Learning to figure out how to set the fastest time on custom grid-based tracks without falling into the void.

## 📦 Installation & Run

1.  **Requirements:** Python 3.6+, Pyglet, and Stable Baselines3.
2.  **Install Libraries:**
    ```bash
    pip install pyglet stable-baselines3[extra] tensorboard
    ```
3.  **Start the AI Observation:**
    ```bash
    python twoj_plik_z_podgladem.py
    ```
4.  **Start AI Training:**
    ```bash
    python train.py
    ```

---

## 🧠 How the AI Learns (Reinforcement Learning)

The car is controlled by a neural network trained using the **PPO (Proximal Policy Optimization)** algorithm. It doesn't know how to drive at first; it learns entirely through trial and error:

* **Observations (Senses):** The AI "sees" the track using raycasts (distance sensors detecting the edge of the track). It also monitors its current speed, grip level, and rotation angle.
* **Actions (Controls):** Based on the observations, the neural network decides whether to press the gas, hit the brakes, or steer left/right.
* **Reward System:** The AI is driven by a strict reward-penalty system. It receives massive penalties for crashing into walls (-100) or standing still, and huge rewards for crossing the finish line (+1000).
* **Dynamic Tweaking (Curriculum Learning):** The training wasn't a simple "set and forget" process. Throughout the learning phases, the reward system and hyperparameters (like entropy/curiosity and gamma) were actively adjusted on the fly. This hands-on approach helped the AI overcome local minima (like spinning in circles or intentionally crashing to minimize point loss) and forced it to learn specific maneuvers step-by-step on custom training tracks.
* **Evolution:** Over millions of simulated frames, the model mathematically adjusts its "brain" weights to avoid negative points and maximize its score, eventually discovering how to drive perfectly and set track records.

---

## 📊 Monitoring Training (TensorBoard)

You can track the AI's learning progress, including its average lap times, survival rate, and entropy (curiosity) in real-time.

To launch the dashboard, open your terminal and run:
```bash
python -m tensorboard.main --logdir=./wyniki_treningu/
```
Once the server starts, open your web browser and go to `http://localhost:6006/`.

---

## 🛠️ Map Editor (Recommended Way)

The game includes a visual Map Editor to make track building easy for the AI.

1.  **Launch the Editor:**
    ```bash
    python map_editor.py
    ```
2.  **Usage:** Select a tool with the keyboard and draw with your mouse.
3.  **Saving:** Press **Ctrl+S** ### Map Editor Controls

| Input          | Action                                                         |
|:---------------|:---------------------------------------------------------------|
| **Left Click** | Place Block (Draw)                                             | 
| **Key '0'** | Erase Block (Void)                                             |
| **Key '1'** | Select **Road** (Full friction)                                |
| **Key '2-9'** | Select **Slippery Road** (2 = Low friction, 9 = High friction) |
| **Key 'F'** | Select **Finish Line** |
| **Key 'R'** | Select **Start Position** |
| **Ctrl + S** | **Save Map** |

---

## 📝 Manual Map Creation (Text File Method)

Alternatively, you can create maps using a simple text editor.

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
```