import psycopg2
import pandas as pd
from geopy.geocoders import Nominatim
import time
import csv
from scipy.spatial import cKDTree
import numpy as np


def augment_train(df_train: pd.DataFrame):
    geolocator = Nominatim(user_agent="trainstation_locator")
    failed = []

    for index, row in df_train.iterrows():
        location = geolocator.geocode(row["station_name"])

        if location:
            df_train.loc[index, 'station_latitude'] = location.latitude
            df_train.loc[index, 'station_longitude'] = location.longitude

            country = location.raw.get("display_name", {}).split()[-1]

            if country == "Deutschland":
                df_train.loc[index, 'trainstation_in_ch'] = False
            elif "Schweiz" in country:
                df_train.loc[index, 'trainstation_in_ch'] = True
            else:
                print(f"trainstation in location {country}")
                df_train.loc[index, 'trainstation_in_ch'] = np.nan

            print(f"found {row["station_name"]} with coords {location.latitude}, {location.longitude}")
        else:
            failed.append(row["station_name"])
            print(f"failed to find {row["station_name"]}")

        time.sleep(1) # This is nessecary to uphold the usage policy of Nominatim

    return failed

def find_weatherstation(df_train_weather: pd.DataFrame, 
                        df_train_de: pd.DataFrame, 
                        df_weather_de: pd.DataFrame, 
                        df_train_ch: pd.DataFrame, 
                        df_weather_ch: pd.DataFrame):

    df_train_weather["trainstation_in_ch"] = False

    # Combine and clean trainstations
    df_train_combined = pd.concat([df_train_de, df_train_ch], ignore_index=True)
    df_train_combined = df_train_combined.dropna(subset=["station_latitude", "station_longitude"])
    df_train_combined = df_train_combined.drop_duplicates().reset_index(drop=True)

    # Combine and clean weatherstations
    df_weather_combined = pd.concat([df_weather_de, df_weather_ch], ignore_index=True)
    df_weather_combined = df_weather_combined.drop_duplicates().reset_index(drop=True)

    # Build KDTree
    weather_tree = cKDTree(df_weather_combined[["station_latitude", "station_longitude"]].values)
    _, index = weather_tree.query(df_train_combined[["station_latitude", "station_longitude"]].values, k=1)

    # Assign trainstation info
    df_train_weather[["trainstation", "trainstation_in_ch"]] = df_train_combined[["trainstation_id", "trainstation_in_ch"]].values

    # Assign weatherstation info
    df_train_weather[["weatherstation", "weatherstation_in_ch"]] = df_weather_combined.iloc[index][["weatherstation_id", "weatherstation_in_ch"]].values


if __name__ == "__main__":
    # Connection settings
    conn = psycopg2.connect(
        dbname="group-05",
        user="postgres",
        password="dbsys2025",
        host="localhost",
        port=5432
    )

    cur = conn.cursor()

    # Queries for getting the Data
    get_german_trainstation = "Select eva, station_name From german_trainstation"
    get_german_weatherstation = "Select station_id, station_latitude, station_longitude From german_weatherstation"

    get_swiss_trainstation = "Select bpuic, station_name From swiss_trainstation"
    get_swiss_weatherstation = "Select station_abbr, station_latitude, station_longitude From swiss_weatherstation"

    # Loading into dataframe
    df_train_de = pd.read_sql_query(get_german_trainstation , conn)

    df_train_de = df_train_de.rename(columns={"eva": "trainstation_id"})
    df_train_de["trainstation_id"] = df_train_de["trainstation_id"].astype(str).str.zfill(8)

    print(df_train_de)

    df_train_de["station_latitude"] = None
    df_train_de["station_longitude"] = None
    df_train_de["trainstation_in_ch"] = False

    df_weather_de = pd.read_sql_query(get_german_weatherstation, conn)

    df_weather_de = df_weather_de.rename(columns={"station_id": "weatherstation_id"})
    df_weather_de["weatherstation_id"] = df_weather_de["weatherstation_id"].astype(str)

    df_weather_de["weatherstation_in_ch"] = False

    df_train_ch = pd.read_sql_query(get_swiss_trainstation, conn)

    df_train_ch = df_train_ch.rename(columns={"bpuic": "trainstation_id"})
    df_train_ch["trainstation_id"] = df_train_ch["trainstation_id"].astype(str)

    df_train_ch["station_latitude"] = None
    df_train_ch["station_longitude"] = None
    df_train_ch["trainstation_in_ch"] = True

    df_weather_ch = pd.read_sql_query(get_swiss_weatherstation, conn)

    df_weather_ch = df_weather_ch.rename(columns={"station_abbr": "weatherstation_id"})
    df_weather_ch["weatherstation_id"] = df_weather_ch["weatherstation_id"].astype(str)
    df_weather_ch["weatherstation_in_ch"] = True

    df_train_weather = pd.DataFrame(columns=["trainstation", "trainstation_in_ch", "weatherstation", "weatherstation_in_ch"])
    df_train_weather = df_train_weather.astype({
        "trainstation": str,
        "trainstation_in_ch": bool,
        "weatherstation": str,
        "weatherstation_in_ch": bool
    })

    # Augment train data
    failed_de = augment_train(df_train_de)
    failed_ch = augment_train(df_train_ch)

    df_train_de = df_train_de.dropna(subset=["trainstation_in_ch"])
    df_train_de = df_train_ch.dropna(subset=["trainstation_in_ch"])

    with open("failed_train_de.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for item in failed_de:
            writer.writerow([item])
    
    with open("failed_train_ch.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for item in failed_ch:
            writer.writerow([item])

    # Create lookup table
    find_weatherstation(df_train_weather, df_train_de, df_weather_de, df_train_ch, df_weather_ch)
    print("assigned trainstations to weatherstations")
    
    df_train_weather.to_csv('trainstation_weatherstation.csv', index = False)
    conn.close()