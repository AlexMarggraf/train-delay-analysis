import pandas as pd
import json
import glob
import os
from datetime import datetime
from pathlib import Path

def clean_data_temp(file, dest_folder, name, historical):
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    df_master = df_master.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    if historical:
        df_master = df_master[df_master["MESS_DATUM"] >= 2024090100].reset_index(drop=True)
        # data only goes till 2025
    else:
        df_master = df_master[
            (df_master["MESS_DATUM"] >= 2025010100) &
            (df_master["MESS_DATUM"] <= 2025090100)
        ].reset_index(drop=True)

    # Required columns to keep a row at all
    required_columns = [
        "STATIONS_ID", "MESS_DATUM", "TT_TU", "RF_TU"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

def clean_data_prec(file, dest_folder, name, historical):
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    df_master = df_master.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    if historical:
        df_master = df_master[df_master["MESS_DATUM"] >= 2024090100].reset_index(drop=True)
        # data only goes till 2025
    else:
        df_master = df_master[
            (df_master["MESS_DATUM"] >= 2025010100) &
            (df_master["MESS_DATUM"] <= 2025090100)
        ].reset_index(drop=True)

    # Required columns to keep a row at all
    required_columns = [
        "STATIONS_ID", "MESS_DATUM", "  R1", "RS_IND", "WRTR" # DO NOT REMOVE THE WHITESPACES
    ]

    print(df_master.columns.tolist())

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

def clean_data_pres(file, dest_folder, name, historical):
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    df_master = df_master.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    if historical:
        df_master = df_master[df_master["MESS_DATUM"] >= 2024090100].reset_index(drop=True)
        # data only goes till 2025
    else:
        df_master = df_master[
            (df_master["MESS_DATUM"] >= 2025010100) &
            (df_master["MESS_DATUM"] <= 2025090100)
        ].reset_index(drop=True)

    # Required columns to keep a row at all
    required_columns = [
        "STATIONS_ID", "MESS_DATUM", "   P", "  P0" # DO NOT REMOVE THE WHITESPACES
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

def clean_data_wind(file, dest_folder, name, historical):
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    df_master = df_master.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    if historical:
        df_master = df_master[df_master["MESS_DATUM"] >= 2024090100].reset_index(drop=True)
        # data only goes till 2025
    else:
        df_master = df_master[
            (df_master["MESS_DATUM"] >= 2025010100) &
            (df_master["MESS_DATUM"] <= 2025090100)
        ].reset_index(drop=True)

    # Required columns to keep a row at all
    required_columns = [
        "STATIONS_ID", "MESS_DATUM", "   F", "   D" # DO NOT REMOVE THE WHITESPACES
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)
   
def station_metadata(file):
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    df_ws = pd.read_csv(
        r"german_weatherstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    df_master = df_master.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    required_columns = [
        "Stations_id", "Stationshoehe", "Geogr.Breite", "Geogr.Laenge", "von_datum", "Stationsname"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)

    df_master = pd.concat([df_master, df_ws], axis=0)
    df_master.drop_duplicates(inplace=True)
    df_master.to_csv("german_weatherstation.csv", index=False)

if __name__ == "__main__":
    weatherstation_columns = ["Stations_id", "Stationshoehe", "Geogr.Breite", "Geogr.Laenge", "von_datum", "bis_datum", "Stationsname"]

    weatherstation_df = pd.DataFrame(columns=weatherstation_columns)
    weatherstation_df.to_csv("german_weatherstation.csv", index=False, encoding="utf-8")
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\air_temperature\historical\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\air_temp"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_temp(file, dest_folder, name, True)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)

    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\air_temperature\recent\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\air_temp"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_temp(file, dest_folder, name, False)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\precipitation\historical\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\precipitation"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_prec(file, dest_folder, name, True)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\precipitation\recent\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\precipitation"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_prec(file, dest_folder, name, False)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\pressure\historical\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\pressure"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_pres(file, dest_folder, name, True)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\pressure\recent\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\pressure"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_pres(file, dest_folder, name, False)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\wind\historical\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\wind"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_wind(file, dest_folder, name, True)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\wind\recent\*/"):
        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\wind"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_wind(file, dest_folder, name, False)

        for file in glob.glob(folder + "Metadaten_Geographie*"):
            station_metadata(file)