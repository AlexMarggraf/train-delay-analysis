import psycopg2
import pandas as pd
from geopy.geocoders import Nominatim
import time
import csv
from scipy.spatial import cKDTree
import numpy as np

def find_weatherstation(df_train_weather: pd.DataFrame, 
                        df_train: pd.DataFrame, 
                        df_weather_de: pd.DataFrame,
                        df_weather_ch: pd.DataFrame):

    # Combine and clean weatherstations
    df_weather_combined = pd.concat([df_weather_de, df_weather_ch], ignore_index=True)
    df_weather_combined = df_weather_combined.drop_duplicates().reset_index(drop=True)

    # Build KDTree
    weather_tree = cKDTree(df_weather_combined[["station_latitude", "station_longitude"]].values)
    _, index = weather_tree.query(df_train[["station_latitude", "station_longitude"]].values, k=1)

    # Create temporary dataframe
    df_tmp = pd.DataFrame(columns=["trainstation", "trainstation_in_ch", "weatherstation", "weatherstation_in_ch"])
    df_tmp = df_tmp.astype({
        "trainstation": str,
        "trainstation_in_ch": bool,
        "weatherstation": str,
        "weatherstation_in_ch": bool
    })

    # Assign trainstation info
    df_tmp[["trainstation", "trainstation_in_ch"]] = df_train[["trainstation_id", "trainstation_in_ch"]].values

    # Assign weatherstation info
    df_tmp[["weatherstation", "weatherstation_in_ch"]] = df_weather_combined.iloc[index][["weatherstation_id", "weatherstation_in_ch"]].values

    # Concatenate both dataframes
    return pd.concat([df_train_weather, df_tmp])


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
    get_german_weatherstation = "Select station_id, station_latitude, station_longitude From german_weatherstation"

    get_swiss_trainstation = "Select bpuic, station_name From swiss_trainstation"
    get_swiss_weatherstation = "Select station_abbr, station_latitude, station_longitude From swiss_weatherstation"

    df_weather_de = pd.read_sql_query(get_german_weatherstation, conn)

    df_weather_de = df_weather_de.rename(columns={"station_id": "weatherstation_id"})
    df_weather_de["weatherstation_id"] = df_weather_de["weatherstation_id"].astype(str)

    df_weather_de["weatherstation_in_ch"] = "False"

    df_train_ch = pd.read_sql_query(get_swiss_trainstation, conn)

    df_train_ch = df_train_ch.rename(columns={"bpuic": "trainstation_id"})
    df_train_ch["trainstation_id"] = df_train_ch["trainstation_id"].astype(str)
    df_train_ch = df_train_ch.drop_duplicates(subset=["station_name"])
    df_train_ch = df_train_ch.reset_index(drop=True)

    df_weather_ch = pd.read_sql_query(get_swiss_weatherstation, conn)

    df_weather_ch = df_weather_ch.rename(columns={"station_abbr": "weatherstation_id"})
    df_weather_ch["weatherstation_id"] = df_weather_ch["weatherstation_id"].astype(str)
    df_weather_ch["weatherstation_in_ch"] = True

    # Load failed trainstations
    df_train = pd.read_csv(
        "manual_train.csv",
        dtype={
            "station_name": str,
            "station_latitude": float,
            "station_longitude": float
        },
        sep=",",
        header=0,
    )

    df_train["trainstation_in_ch"] = True
    df_train = df_train.rename(columns={"station_name": "trainstation_id"})

    eva_map = df_train_ch.set_index("station_name")["trainstation_id"]
    df_train["trainstation_id"] = df_train["trainstation_id"].map(eva_map)

    # Load existing lookup table
    df_train_weather = pd.read_csv(
        "trainstation_weatherstation.csv",
        dtype={
            "trainstation": str,
            "trainstation_in_ch": bool,
            "weatherstation": str,
            "weatherstation_in_ch": bool
        },
        sep=",",
        header=0,
    )

    # Augment lookup table
    df_train_weather = find_weatherstation(df_train_weather, df_train, df_weather_de, df_weather_ch)
    df_train_weather.to_csv("trainstation_weatherstation.csv", index=False)
    
    conn.close()