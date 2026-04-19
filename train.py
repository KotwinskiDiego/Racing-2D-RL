from car_env import CarEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback, CallbackList
import datetime
import os

# --- NASZA WTYCZKA DO WYKRESÓW ---
class TimeLogCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)

    def _on_step(self) -> bool:
        if "infos" in self.locals:
            for info in self.locals["infos"]:
                if "lap_time" in info:
                    self.logger.record("custom/czas_okrazenia_sekundy", info["lap_time"])
        return True

os.makedirs("zapisani_kierowcy", exist_ok=True)

czas_startu = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
nazwa_modelu = f"kierowca_{czas_startu}"

# =====================================================================
# ZMIENNA DO KONTYNUACJI TRENINGU
# Wpisz tu ścieżkę do modelu, np. "./zapisani_kierowcy/kierowca_wczoraj.zip"
# Jeśli chcesz zacząć od nowa, zostaw None
# =====================================================================
STARY_MODEL_PATH = "zapisani_kierowcy/checkpoints/kierowca_2026-04-19_20-18_4100704_steps.zip"  # Zmień na ścieżkę, by kontynuować, np. "zapisani_kierowcy/kierowca_2026-04-19_14-30_final.zip"

print(f"Sesja treningowa: {nazwa_modelu}")

env = CarEnv("tor3.txt")

checkpoint_callback = CheckpointCallback(
    save_freq=100000,
    save_path="./zapisani_kierowcy/checkpoints/",
    name_prefix=nazwa_modelu
)

time_log_callback = TimeLogCallback()
callback_list = CallbackList([checkpoint_callback, time_log_callback])

# =====================================================================
# ŁADOWANIE LUB TWORZENIE MODELU
# =====================================================================

nowe_parametry = {"gamma":0.95,"ent_coef":0.01}
if STARY_MODEL_PATH is not None and os.path.exists(STARY_MODEL_PATH):
    print(f"Wczytywanie istniejącego modelu z: {STARY_MODEL_PATH}...")
    # Ładujemy model i podpinamy go pod nowe środowisko i tensorboard
    model = PPO.load(STARY_MODEL_PATH, env=env, tensorboard_log="./wyniki_treningu/",custom_objects=nowe_parametry)
else:
    print("Tworzenie zupełnie nowego agenta od zera...")
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./wyniki_treningu/",custom_objects=nowe_parametry)

# Odpalamy trening!
# UWAGA: reset_num_timesteps=False sprawia, że jeśli stary model miał już 1 mln kroków,
# to nowe logi w Tensorboardzie zaczną się rysować od 1 miliona, zachowując ciągłość wykresu!
print("Rozpoczynam jazdę...")
model.learn(
    total_timesteps=1000000,
    callback=callback_list,
    tb_log_name=nazwa_modelu,
    reset_num_timesteps=False

)

koncowa_sciezka = f"./zapisani_kierowcy/{nazwa_modelu}_final"
model.save(koncowa_sciezka)
print(f"Trening zakończony! Model zapisany jako: {koncowa_sciezka}")