import psycopg2
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import time
import csv


def augment_train(df_train: pd.DataFrame):
    geolocator = Nominatim(user_agent="trainstation_locator")
    failed = []

    for index, row in df_train.iterrows():
        location = geolocator.geocode(row["station_name"])

        if location:
            df_train.loc[index, 'station_latitude'] = location.latitude
            df_train.loc[index, 'station_longitude'] = location.longitude
            print(f"found {row["station_name"]}")
        else:
            failed.append(row["station_name"])
            print(f"failed to find {row["station_name"]}")

        time.sleep(1) # This is nessecary to uphold the usage policy of Nominatim

    return failed

def train_to_lk(df_train: pd.DataFrame):
    gdf_train = gpd.GeoDataFrame(
        df_train,
        geometry=[Point(xy) for xy in zip(df_train.station_longitude, df_train.station_latitude)],
        crs="EPSG:4326"
    )

    lk = gpd.read_file("analysis/VG2500_KRS.shp").to_crs("EPSG:4326")

    mapping = gpd.sjoin(
        gdf_train,
        lk,
        how="inner",
        predicate="within"
    )

    return mapping

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

    # Loading into dataframe
    df_train_de = pd.read_sql_query(get_german_trainstation , conn)
    df_train_de["station_latitude"] = None
    df_train_de["station_longitude"] = None

    _ = augment_train(df_train_de)
    map = train_to_lk(df_train_de)
    map = map[["eva", "AGS", "GEN"]]

    map.to_csv("train-to-lk.csv", index=False)

    conn.close()