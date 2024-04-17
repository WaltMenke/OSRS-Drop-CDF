from osrsbox import monsters_api
from dash import Dash, html, dcc, callback, Output, Input
import numpy as np
import plotly.express as px
import pandas as pd
import sys

monsters = monsters_api.load()
initial_monster = "zulrah"
initial_item = "tanzanite fang"

num_kills = 2000
num_simulations = 1000
num_bins = 100
desired_rate = 0.8

if __name__ == "__main__":
    all_db_monsters = monsters_api.load()
    # Search for the monster
    srch_monstr = next(
        (
            monster
            for monster in all_db_monsters
            if monster.name.lower() == initial_monster.lower()
        ),
        None,
    )

    if srch_monstr:
        print(f"{srch_monstr.name} found in the database.")
    else:
        print(f"{initial_monster} not found in the database.")
        sys.exit(1)

    # Search for the item
    srch_item = next(
        (
            item
            for item in srch_monstr.drops
            if item.name.lower() == f"{initial_item.lower()}"
        ),
        None,
    )

    if srch_item:
        print(f"Name: {srch_item.name}, Rarity: 1/{int(1/srch_item.rarity)}")
    else:
        print(f"{initial_item} not found in the {srch_monstr}'s database.")
        sys.exit(1)

    results = []

    for _ in range(num_simulations):
        trials_to_success = np.random.geometric(srch_item.rarity, num_kills)
        results.append(trials_to_success)

    results_array = np.array(results)

    results_array_reshaped = results_array.reshape(num_simulations, num_kills, 1)

    cumulative_probability = np.mean(
        results_array_reshaped <= np.arange(1, num_kills + 1), axis=1
    )

    data = {
        "Number of Kills": np.arange(1, num_kills + 1),
        "Cumulative Probability": np.mean(cumulative_probability, axis=0),
    }
    df = pd.DataFrame(data)

    filt_df = df[df["Cumulative Probability"] > desired_rate]

    if not filt_df.empty:
        kill_threshold = filt_df.iloc[0, 0]
        print(
            f"You have an {desired_rate*100}% chance of receiving your item at {kill_threshold} kills."
        )
    else:
        print(
            f"No occurrence found where cumulative probability is greater than {desired_rate} for {num_kills} kills."
        )
