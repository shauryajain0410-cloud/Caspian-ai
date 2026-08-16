from pathlib import Path

import pandas as pd

# Load relative to this file's location, not the process's current working
# directory, so this works no matter where the bot is launched from.
CSV_PATH = Path(__file__).resolve().parent / "clean_travel_data.csv"

df = pd.read_csv(CSV_PATH)
