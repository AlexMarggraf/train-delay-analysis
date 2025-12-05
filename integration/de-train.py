import pandas as pd
import glob
import os
from pathlib import Path

def separate_data(file, dest_folder, date):
    # Load data csv file into dataframe
    df_master = pd.read_csv(file)

    # Load german trainstation csv file into dataframe
    df_trainstation = pd.read_csv(
        r"german_trainstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Load german trainline csv file into dataframe
    df_line = pd.read_csv(
        r"german_line.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Set datatype of eva, otherwise leading 0 get removed because python thinks its an integer
    df_master["eva"] = df_master["eva"].astype("string")
    df_trainstation["eva"] = df_trainstation["eva"].astype("string")

    # Required columns to keep a row at all
    required_columns = [
        "station_name",
        "eva",
        "train_line_ride_id",
        "final_destination_station",
        "train_name",
        "id",
    ]

    # Replace empty strings with NA so they get dropped later
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns)

    # Columns of trainstation dataframe
    trainstation = (
        df_master[["eva", "station_name", "xml_station_name"]]
    )

    # Concatenate already existing trainstations with new trainstations
    trainstation = pd.concat([trainstation, df_trainstation], axis=0)

    # Again set eva to be a string and fill with 0 just to be sure
    trainstation["eva"] = trainstation["eva"].astype("string")
    trainstation["eva"] = trainstation["eva"].str.zfill(8)

    # Remove dublicates and save dataframe in file
    trainstation.drop_duplicates(subset=["eva"], inplace=True)
    trainstation.to_csv("german_trainstation.csv", index=False)

    # Columns for trainline dataframe
    line = (
        df_master[[
            "train_line_ride_id", "final_destination_station",
            "train_name", "train_type"
        ]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Concatenate already existing trainlines with new trainlines
    line = pd.concat([df_line, line], axis=0)

    # Make sure train line ride id is an integer
    line["train_line_ride_id"] = line["train_line_ride_id"].astype(int)

    # Drop dublicates and save dataframe
    line = line.drop_duplicates().reset_index(drop=True)
    line.to_csv("german_line.csv", index=False)

    # Columns for trainstop dataframe
    stop = (
        df_master[[
            "id", "eva", "train_line_ride_id",
            "final_destination_station", "train_name",
            "arrival_change_time", "departure_change_time",
            "arrival_planned_time","departure_planned_time",
            "delay_in_min", "time", "is_canceled",
            "train_line_station_num"
        ]]

        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Make sure eva is a string and fill with 0 just to be sure
    stop["eva"] = stop["eva"].astype("string")
    stop["eva"] = stop["eva"].str.zfill(8)

    # Make sure train line ride id is an integer
    stop["train_line_ride_id"] = stop["train_line_ride_id"].astype(int)

    # Save trainstop dataframe in file
    stop.to_csv(f"{dest_folder}/stop-{date}.csv", index=False)

    print("✓ All tables successfully generated")

if __name__ == "__main__":
    # Generate trainstop and trainline files
    trainstation_columns = ["eva", "station_name", "xml_station_name"]

    trainstation_df = pd.DataFrame(columns=trainstation_columns)
    trainstation_df.to_csv("german_trainstation.csv", index=False, encoding="utf-8")

    line_cols = ["train_line_ride_id", "final_destination_station", "train_name", "train_type",]

    line_df = pd.DataFrame(columns=line_cols)
    line_df.to_csv("german_line.csv", index=False, encoding="utf-8")

    # Loop over all german traindata csv files
    for file in glob.glob(r"Deutschland\DB\monthly_processed_data\*.csv", recursive=True):
        print("Processing:", file)

        filepath = Path(file)
        date = filepath.stem

        dest_folder = f"processed\db\processed"
        os.makedirs(dest_folder, exist_ok=True)

        # Clean data
        separate_data(file, dest_folder, date)

    # Loading trainline file into dataframe
    final_line = pd.read_csv(
        r"german_line.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Final Deduplication to make sure and then save file
    final_line.drop_duplicates(inplace=True)
    final_line.to_csv("processed/db/german_line.csv", index=False)