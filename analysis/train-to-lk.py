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
            row_failed = df_failed_train[df_failed_train['station_name'] == row["station_name"]]

            if not row_failed.empty:
                df_train.loc[index, 'station_latitude'] = row_failed.iloc[0]["station_latitude"]
                df_train.loc[index, 'station_longitude'] = row_failed.iloc[0]["station_longitude"]
            else:
                raise Exception("Could not find trainstation in manual_train.csv")

        time.sleep(1) # This is nessecary to uphold the usage policy of Nominatim

    return failed

def train_to_lk(df_train: pd.DataFrame, ch=True):
    gdf_train = gpd.GeoDataFrame(
        df_train,
        geometry=[Point(xy) for xy in zip(df_train.station_longitude, df_train.station_latitude)],
        crs="EPSG:4326"
    )

    if ch:
        shape = gpd.read_file("analysis\ch\swissBOUNDARIES3D_1_5_TLM_KANTONSGEBIET.shp").to_crs("EPSG:4326")
    else:
        shape = gpd.read_file("analysis/de/VG2500_KRS.shp").to_crs("EPSG:4326")

    mapping = gpd.sjoin(
        gdf_train,
        shape,
        how="inner",
        predicate="intersects"
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
    get_swiss_trainstation = "Select bpuic, station_name From swiss_trainstation"

    get_map = "Select trainstation, trainstation_in_ch From trainstation_weatherstation"

    # Loading into dataframe
    df_train_de = pd.read_sql_query(get_german_trainstation , conn)
    df_train_de["station_latitude"] = None
    df_train_de["station_longitude"] = None

    df_train_de = df_train_de.rename(columns={"eva": "trainstation"})
    df_train_de["trainstation"] = df_train_de["trainstation"].astype(str).str.zfill(8)

    df_train_ch = pd.read_sql_query(get_swiss_trainstation , conn)
    df_train_ch["station_latitude"] = None
    df_train_ch["station_longitude"] = None

    df_train_ch = df_train_ch.rename(columns={"bpuic": "trainstation"})
    df_train_ch["trainstation"] = df_train_ch["trainstation"].astype(str)

    df_map = pd.read_sql_query(get_map, conn)

    train_df = pd.concat([df_train_de, df_train_ch], ignore_index = True)

    train_df = pd.merge(
        train_df,
        df_map,
        on='trainstation',
        how='inner'
        )

    train_df = train_df.dropna(subset=["trainstation_in_ch"])

    df_train_de = train_df[train_df["trainstation_in_ch"] == False]
    df_train_ch = train_df[train_df["trainstation_in_ch"] == True]

    df_failed_train = pd.read_csv(
        "manual_train.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    _ = augment_train(df_train_de)
    _ = augment_train(df_train_ch)

    print(df_train_ch)

    map_de = train_to_lk(df_train_de, ch=False)
    map_ch = train_to_lk(df_train_ch, ch=True)

    map_de = map_de[["trainstation", "AGS", "GEN"]]
    map_ch = map_ch[["trainstation", "UUID", "NAME"]]

    map_de = map_de.rename(columns={"AGS": "id", "GEN" : "NAME"})
    map_ch = map_ch.rename(columns={"UUID": "id"})

    map_de.to_csv("choropleth_de.csv", index=False)
    map_ch.to_csv("choropleth_ch.csv", index=False)

    conn.close()