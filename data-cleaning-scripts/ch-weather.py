import pandas as pd
import json
import glob
import os
from datetime import datetime
from pathlib import Path

def clean_data(file, dest_folder, name):
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
    )

    print(df_master.columns.tolist())

    df_master["reference_timestamp"] = pd.to_datetime(df_master["reference_timestamp"], format="%d.%m.%Y %H:%M")

    start = pd.to_datetime("01.09.2024 00:00", format="%d.%m.%Y %H:%M")
    end   = pd.to_datetime("31.08.2025 23:59", format="%d.%m.%Y %H:%M")

    df_master = df_master[(df_master["reference_timestamp"] >= start) & (df_master["reference_timestamp"] <= end)].reset_index(drop=True)

    # Required columns to keep a row at all
    required_columns = [
        "station_abbr", "reference_timestamp"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

if __name__ == "__main__":
    for file in glob.glob(r"Schweiz\MeteoCH\**\*.csv", recursive=True):
        filepath = Path(file)
        name = filepath.stem

        dest_folder = r"processed"
        os.makedirs(dest_folder, exist_ok=True)

        clean_data(file, dest_folder, name)