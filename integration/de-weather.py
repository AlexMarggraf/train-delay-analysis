import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path

# Function for cleaning german air temperature data
def clean_data_temp(file, dest_folder, name, historical):
    # Load data text file into dataframe
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    # Remove trailing and leading whitespaces
    df_master.columns = df_master.columns.str.strip()

    # Strip all strings of leading and trailing whitespaces
    df_master = df_master.map(lambda x: x.strip() if isinstance(x, str) else x)

    # Store measurement date as integer
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    # Make sure data is within the correct timespan
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
        "STATIONS_ID", "MESS_DATUM"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)

    # Some weatherstations are not measuring anymore so this is needed
    if df_master.empty:
        return

    # Set impossibel datapoints to NaN
    df_master.loc[df_master["RF_TU"] < 0, "RF_TU"] = np.nan
    df_master.loc[df_master["RF_TU"] > 100, "RF_TU"] = np.nan

    df_master.loc[df_master["TT_TU"] < -100, "TT_TU"] = np.nan
    df_master.loc[df_master["TT_TU"] > 100, "TT_TU"] = np.nan

    # Format date
    df_master["MESS_DATUM"] = pd.to_datetime(df_master["MESS_DATUM"], format="%Y%m%d%H", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    # Save file
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

# Function for cleaning german rain data
def clean_data_prec(file, dest_folder, name, historical):
    # Load german rain data text file
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    # Remove leading and trailing whitespaces
    df_master.columns = df_master.columns.str.strip()

    # Strip all strings of leading and trailing whitespaces
    df_master = df_master.map(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Store measurement date as integer
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    # Make sure data is in the correct timespan
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
        "STATIONS_ID", "MESS_DATUM"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)

    # Some weatherstations are not measuring anymore so this is needed
    if df_master.empty:
        return
    
    # Convert from float to int
    df_master["WRTR"] = pd.to_numeric(df_master["WRTR"], errors="coerce").astype("Int64")

    # Convert from int to boolean
    df_master["RS_IND"] = df_master["RS_IND"].astype(bool)

    # Set impossible measurements to Nan
    df_master.loc[df_master["R1"] < 0, "R1"] = np.nan
    df_master.loc[df_master["R1"] > 500, "R1"] = np.nan

    df_master.loc[df_master["RS_IND"] < 0, "RS_IND"] = np.nan
    df_master.loc[df_master["RS_IND"] > 1, "RS_IND"] = np.nan

    df_master.loc[df_master["WRTR"] < 0, "WRTR"] = np.nan
    df_master.loc[df_master["WRTR"] > 100, "WRTR"] = np.nan

    # Format date
    df_master["MESS_DATUM"] = pd.to_datetime(df_master["MESS_DATUM"], format="%Y%m%d%H", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    # Store file
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

# Function for cleaning german pressure data
def clean_data_pres(file, dest_folder, name, historical):
    # Load data file into dataframe
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    # Remove trailing and leading whitespaces
    df_master.columns = df_master.columns.str.strip()

    # Strip strings of leading and trailing whitespaces
    df_master = df_master.map(lambda x: x.strip() if isinstance(x, str) else x)

    # Store measurement date as integer
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    # Make sure data is in correct timespan
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
        "STATIONS_ID", "MESS_DATUM"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)

    # Nessecary since some weatherstations stopped measuring
    if df_master.empty:
        return

    # Set impossible datapoints to NaN
    df_master.loc[df_master["P"] < 800, "P"] = np.nan
    df_master.loc[df_master["P"] > 1100, "P"] = np.nan

    df_master.loc[df_master["P0"] < 800, "P0"] = np.nan
    df_master.loc[df_master["P0"] > 1100, "P0"] = np.nan

    # Format date
    df_master["MESS_DATUM"] = pd.to_datetime(df_master["MESS_DATUM"], format="%Y%m%d%H", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    # Save dataframe as file
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

# Function to clean german wind data
def clean_data_wind(file, dest_folder, name, historical):
    # Load data file into dataframe
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )
    
    # Remove leading and trailing whitespaces
    df_master.columns = df_master.columns.str.strip()

    # Strip strings of leading and trailing whitespaces
    df_master = df_master.map(lambda x: x.strip() if isinstance(x, str) else x)

    # Store measurement date as an integer
    df_master["MESS_DATUM"] = df_master["MESS_DATUM"].astype(int)

    # Only keep data in the correct timespan
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
        "STATIONS_ID", "MESS_DATUM"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)
    df_master.drop_duplicates(inplace=True)

    # Needed since some weatherstations stopped measuring
    if df_master.empty:
        return
    
    df_master["D"] = pd.to_numeric(df_master["D"], errors="coerce").astype("Int64")

    # Set impossible datapoints to NaN
    df_master.loc[df_master["F"] < 0, "F"] = np.nan
    df_master.loc[df_master["F"] > 200, "F"] = np.nan

    df_master.loc[df_master["D"] < 0, "D"] = np.nan
    df_master.loc[df_master["D"] > 360, "D"] = np.nan

    # Format measurement date
    df_master["MESS_DATUM"] = pd.to_datetime(df_master["MESS_DATUM"], format="%Y%m%d%H", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    # Save dataframe as file
    df_master.to_csv(f"{dest_folder}/{name}.csv", index=False)

# Function to store the weatherstations
def station_metadata(file):
    # Load data file into dataframe
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    # Remove leading and trailing whitespaces
    df_master.columns = df_master.columns.str.strip()
    
    # Only keep the last record of the station
    df_master = df_master.tail(1)

    # Store to date as integer
    df_master["bis_datum"] = pd.to_numeric(df_master["bis_datum"], errors="coerce")

    # If last station record stopped before 01.09.2024 return
    if df_master["bis_datum"].iat[-1] is not None and df_master["bis_datum"].iat[-1] < 20240901:
        return

    # Load already exisitng weatherstations into a dataframe
    df_ws = pd.read_csv(
        r"german_weatherstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Strip strings of leading and trailing whitespaces
    df_master = df_master.map(lambda x: x.strip() if isinstance(x, str) else x)

    # Format date
    df_master["von_datum"] = pd.to_datetime(df_master["von_datum"], format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    df_master["bis_datum"] = pd.to_datetime(df_master["bis_datum"], format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d").fillna("")

    # Required columns to keep row at all
    required_columns = [
        "Stations_id"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns).reset_index(drop=True)

    # Concatenate already existing weatherstations and new weatherstations
    df_master = pd.concat([df_master, df_ws], axis=0)

    # Drop duplicates. Subset is nessecary here because some stations
    # measure more than just one parameter.
    df_master.drop_duplicates(subset=["Stations_id"], inplace=True)

    # Store dataframe in file
    df_master.to_csv("german_weatherstation.csv", index=False)

if __name__ == "__main__":
    # Create weatherstation file
    weatherstation_columns = ["Stations_id", "Stationshoehe", "Geogr.Breite", "Geogr.Laenge", "von_datum", "bis_datum", "Stationsname" ]

    weatherstation_df = pd.DataFrame(columns=weatherstation_columns)
    weatherstation_df.to_csv("german_weatherstation.csv", index=False, encoding="utf-8")

    # Loop over all folders, clean data and then store
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\air_temperature\historical\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\air_temp"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_temp(file, dest_folder, name, True)

    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\air_temperature\recent\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\air_temp"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_temp(file, dest_folder, name, False)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\precipitation\historical\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\precipitation"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_prec(file, dest_folder, name, True)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\precipitation\recent\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\precipitation"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_prec(file, dest_folder, name, False)

    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\pressure\historical\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\pressure"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_pres(file, dest_folder, name, True)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\pressure\recent\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\pressure"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_pres(file, dest_folder, name, False)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\wind\historical\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\wind"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_wind(file, dest_folder, name, True)
    
    for folder in glob.glob(r"Deutschland\DWD\dwd_filtered\wind\recent\*/"):
        for file in glob.glob(folder + "Metadaten_Geographie*"):
            from_date = station_metadata(file)

        for file in glob.glob(folder + "produkt*"):
            filepath = Path(file)
            name = filepath.stem

            dest_folder = r"processed\dwd\wind"
            os.makedirs(dest_folder, exist_ok=True)

            clean_data_wind(file, dest_folder, name, False)

    # Load german weatherstation file into dataframe
    station_final = pd.read_csv(
        r"german_weatherstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False,
        encoding='latin1'
    )

    # last deduplication and storing.
    station_final.drop_duplicates(subset=["Stations_id"], inplace=True)
    station_final.to_csv("processed/dwd/german_weatherstation.csv", index=False)

