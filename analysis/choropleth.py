import psycopg2
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors

def choropleth_de():
    get_station_delay_ch = """
        SELECT bpuic as trainstation, EXTRACT(EPOCH FROM AVG(predicted_departure - departure_time)) / 60 as delay
        FROM swiss_trainstop
        WHERE predicted_departure IS NOT NULL
            AND departure_time IS NOT NULL
            AND cancellation_flag = false
            AND pass_through_flag = false
        GROUP BY bpuic
    """

    get_station_delay_de = """
        SELECT eva AS trainstation, AVG(delay_in_min)
        FROM german_trainstop
        WHERE delay_in_min IS NOT NULL AND is_canceled = false
        GROUP BY eva
        """
    
    station_delay_ch = pd.read_sql_query(get_station_delay_ch, conn)
    station_delay_ch["trainstation"] = station_delay_ch["trainstation"].astype(str)

    station_delay_de = pd.read_sql_query(get_station_delay_de, conn)
    station_delay_de["trainstation"] = station_delay_de["trainstation"].astype(str).str.zfill(8)

    station_to_lk = pd.read_csv(
        "choropleth_de.csv",
        dtype={"trainstation": "string", "id": "string"},
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    map_de = pd.merge(
        station_delay_de,
        station_to_lk,
        on="trainstation",
        how="inner"
    )

    map_ch = pd.merge(
        station_delay_ch,
        station_to_lk,
        on="trainstation",
        how="inner"
    )

    map_ch = map_ch.rename(columns={"delay": "avg"})

    map = pd.concat([map_de, map_ch])
    map.to_csv("analysis/choropleth/avg_delay_de.csv", index=False)
    map = map[["id", "avg"]]

    map = (
        map
        .groupby("id", as_index=False)
        .agg(avg=("avg", "mean"))
    )

    shape_de = gpd.read_file("analysis\de\VG2500_KRS.shp")
    shape_de["AGS"] = shape_de["AGS"].astype(str)

    shape_de = shape_de.merge(
        map_de,
        left_on="AGS",
        right_on="id",
        how="left"
    )

    _, ax = plt.subplots(figsize=(4, 4.8))

    shape_de.plot(
        column="avg",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        missing_kwds={
            "color": "darkgrey",
            "label": "No data"
        },
        ax=ax
    )

    ax.set_title("Average Train Delay (minutes)")
    ax.axis("off")

    plt.savefig("analysis/choropleth/avg_delay_de.png", dpi=512)
    plt.savefig("analysis/choropleth/avg_delay_de.svg")

def choropleth_ch():
    get_station_delay_ch = """
        SELECT bpuic as trainstation, EXTRACT(EPOCH FROM AVG(predicted_departure - departure_time)) / 60 as delay
        FROM swiss_trainstop
        WHERE predicted_departure IS NOT NULL
            AND departure_time IS NOT NULL
            AND cancellation_flag = false
            AND pass_through_flag = false
        GROUP BY bpuic
    """
    
    station_delay_ch = pd.read_sql_query(get_station_delay_ch, conn)
    station_delay_ch["trainstation"] = station_delay_ch["trainstation"].astype(str)

    station_to_canton = pd.read_csv(
        "choropleth_ch.csv",
        dtype={"trainstation": "string", "id": "string"},
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    map = pd.merge(
        station_delay_ch,
        station_to_canton,
        on="trainstation",
        how="inner"
    )

    map = map.rename(columns={"delay": "avg"})
    map.to_csv("analysis/choropleth/avg_delay_ch.csv", index=False)
    map = map[["avg", "id"]]

    map = (
        map
        .groupby("id", as_index=False)
        .agg(avg=("avg", "mean"))
    )

    shape_ch = gpd.read_file("analysis\ch\swissBOUNDARIES3D_1_5_TLM_KANTONSGEBIET.shp")

    shape_ch = shape_ch.merge(
        map,
        left_on="UUID",
        right_on="id",
        how="left"
    )

    shape_ch["avg"] = np.clip(shape_ch["avg"], None, 6)

    _, ax = plt.subplots(figsize=(4.8, 3.06))

    shape_ch.plot(
        column="avg",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        # norm = colors.PowerNorm(gamma=0.4, vmin=shape_ch["avg"].min(), vmax=shape_ch["avg"].max()),
        missing_kwds={
            "color": "drakgrey",
            "label": "No data"
        },
        ax=ax
    )

    ax.set_title("Average Train Delay (minutes)")
    ax.axis("off")

    plt.savefig("analysis/choropleth/avg_delay_ch.png", dpi=512)
    plt.savefig("analysis/choropleth/avg_delay_ch.svg")

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
    choropleth_de()
    choropleth_ch()
    