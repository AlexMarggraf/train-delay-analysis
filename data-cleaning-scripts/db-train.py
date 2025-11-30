import pandas as pd
import json
import glob
import os
from datetime import datetime
from pathlib import Path

def separate_data(file, dest_folder, date):
    # -----------------------------
    # 1. LOAD CSV AND FILTER
    # -----------------------------
    df_master = pd.read_parquet(file)

    df_trainstation = pd.read_csv(
        r"german_trainstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Required columns to keep a row at all
    required_columns = [
        "station_name", "delay_in_min",
        "time", "is_canceled",
        "train_line_ride_id", "arrival_planned_time",
        "arrival_change_time", "departure_planned_time",
        "departure_change_time", "id",
    ]

    # replace empty strings with NA so they get dropped later
    df_master["train_line_ride_id"] = df_master["train_line_ride_id"].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns)

    # use this to check the cleaned dataframe
    # df_master.to_csv("control_cleaned.csv", index=False)
    # print("✓ Cleaned master saved as control_cleaned.csv")
    # print(df_master[required_columns].isna().sum())


    # ---------------------------------------------------------
    # 2. TABLE GENERATION — CLEAN, DEDUPED, RELATIONAL STRUCTURE
    # ---------------------------------------------------------

    # -----------------------------
    # Table: Trainstation
    # -----------------------------
    trainstation = (
        df_master[["station_name", "eva", "xml_station_name"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    trainstation = pd.concat([trainstation, df_trainstation], axis=0)
    trainstation.drop_duplicates(inplace=True)
    trainstation.to_csv("german_trainstation.csv", index=False)

    # print("✓ Saved Trainstation.csv")

    # -----------------------------
    # Table: Line
    # -----------------------------
    line = (
        df_master[[
            "train_line_ride_id", "final_destination_station",
            "train_type", "train_name"
        ]]
        .drop_duplicates()
    )
    line.to_csv(f"{dest_folder}/line-{date}.csv", index=False)
    # print("✓ Saved Line.csv")


    # -----------------------------
    # Table: Stop (base type)
    # -----------------------------
    stop = (
        df_master[[
            "id", "station_name", "train_line_ride_id",
            "arrival_planned_time", "arrival_change_time",
            "departure_planned_time", "departure_change_time",
            "delay_in_min", "time", "is_canceled",
            "train_line_station_num"
        ]]
        .drop_duplicates()
    )

    stop.to_csv(f"{dest_folder}/stop-{date}.csv", index=False)
    # print("✓ Saved Stop.csv")

    print("✓ All tables successfully generated")

if __name__ == "__main__":

    trainstation_columns = ["station_name"]

    trainstation_df = pd.DataFrame(columns=trainstation_columns)
    trainstation_df.to_csv("german_trainstation.csv", index=False, encoding="utf-8")

    for file in glob.glob(r"Deutschland\DB\monthly_processed_data\*.parquet", recursive=True):
        print("Processing:", file)

        filepath = Path(file)
        date = filepath.stem

        dest_folder = f"db\processed"
        os.makedirs(dest_folder, exist_ok=True)

        separate_data(file, dest_folder, date)
