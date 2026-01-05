import psycopg2
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.ticker import MaxNLocator

def choropleth_de():
    get_station_delay_ch = """
        SELECT
            bpuic AS trainstation,
            EXTRACT(EPOCH FROM AVG(predicted_arrival - arrival_time)) / 60 AS delay,
            COUNT(*) AS entries
        FROM swiss_trainstop
            WHERE predicted_arrival IS NOT NULL
            AND arrival_time IS NOT NULL
            AND cancellation_flag = false
            AND pass_through_flag = false
        GROUP BY bpuic;
    """

    get_station_cancellation_ch = """
        Select 
            bpuic As trainstation,
            SUM(Case When cancellation_flag = True Then 1 Else 0 End) as canceled,
            SUM(Case When cancellation_flag = False Then 1 Else 0 End) as not_canceled
        From swiss_trainstop
        Where pass_through_flag = false
            AND cancellation_flag Is Not Null
        Group By trainstation
    """

    get_station_delay_de = """
        SELECT eva AS trainstation, AVG(delay_in_min) AS delay, COUNT(*) as entries
        FROM german_trainstop
        WHERE delay_in_min IS NOT NULL AND is_canceled = false
        GROUP BY eva
        """
    get_station_cancellation_de = """
        Select 
            eva as trainstation,
            Sum(Case When is_canceled = True Then 1 Else 0 End) as canceled,
            Sum(Case When is_canceled = False Then 1 Else 0 End) as not_canceled
        From german_trainstop
        Where is_canceled Is Not Null
        Group By trainstation
    """
    
    station_delay_ch = pd.read_sql_query(get_station_delay_ch, conn)
    station_delay_ch.loc[station_delay_ch["delay"] < -1000, "delay"] += 1440
    station_delay_ch["delay"] = station_delay_ch["delay"].clip(lower=0)
    station_delay_ch["trainstation"] = station_delay_ch["trainstation"].astype(str)

    station_canceled_ch = pd.read_sql_query(get_station_cancellation_ch, conn)
    station_canceled_ch["trainstation"] = station_canceled_ch["trainstation"].astype("str")

    station_delay_de = pd.read_sql_query(get_station_delay_de, conn)
    station_delay_de["delay"] = station_delay_de["delay"].clip(lower=0)
    station_delay_de["trainstation"] = station_delay_de["trainstation"].astype(str).str.zfill(8)

    station_canceled_de = pd.read_sql_query(get_station_cancellation_de, conn)
    station_canceled_de["trainstation"] = station_canceled_de["trainstation"].astype("str").str.zfill(8)

    station_to_lk = pd.read_csv(
        "choropleth_de.csv",
        dtype={"trainstation": "string", "id": "string"},
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    map_de = (
        station_delay_de
        .merge(station_canceled_de, on="trainstation", how="inner")
        .merge(station_to_lk, on="trainstation", how="inner")
    )

    map_ch = (
        station_delay_ch
        .merge(station_canceled_ch, on="trainstation", how="inner")
        .merge(station_to_lk, on="trainstation", how="inner")
    )

    map = pd.concat([map_de, map_ch])

    map["delay"] = map["delay"] * map["entries"]

    map = (
        map
        .groupby("id", as_index=False)
        .agg(
            average_delay=("delay", "sum"),
            canceled=("canceled", "sum"),
            not_canceled=("not_canceled", "sum"),
            train_stops=("entries", "sum"),
            municipality=("NAME", "first")
            )
    )

    map["average_delay"] = map["average_delay"] / map["train_stops"]
    map["canceled"] = 100 * map["canceled"] / (map["canceled"] + map["not_canceled"])

    shape_de = gpd.read_file("analysis\de\VG2500_KRS.shp")
    shape_de["AGS"] = shape_de["AGS"].astype(str)

    shape_de = shape_de.merge(
        map,
        left_on="AGS",
        right_on="id",
        how="left"
    )

    _, ax = plt.subplots(figsize=(4.8, 5.76))

    shape_de.plot(
        column="average_delay",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        norm = colors.PowerNorm(gamma=0.3, vmin=shape_de["average_delay"].min(), vmax=shape_de["average_delay"].max()),
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

    plt.close()
    _, ax = plt.subplots(figsize=(4.8, 5.76))

    shape_de.plot(
        column="train_stops",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        norm = colors.PowerNorm(gamma=0.3, vmin=shape_de["train_stops"].min(), vmax=shape_de["train_stops"].max()),
        missing_kwds={
            "color": "darkgrey",
            "label": "No data"
        },
        ax=ax
    )

    ax.set_title("Total Train Stops")
    ax.axis("off")

    plt.savefig("analysis/choropleth/tot_stops_de.png", dpi=512)
    plt.savefig("analysis/choropleth/tot_stops_de.svg")

    plt.close()
    _, ax = plt.subplots(figsize=(4.8, 5.76))

    shape_de.plot(
        column="canceled",
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

    ax.set_title("Average Train Cancelation (percentage)")
    ax.axis("off")

    plt.savefig("analysis/choropleth/avg_canceled_de.png", dpi=512)
    plt.savefig("analysis/choropleth/avg_canceled_de.svg")

    plt.close()

    map = map.rename(columns={"canceled": "average_cancelation"})

    map = map[["municipality", "average_cancelation", "average_delay", "train_stops"]]
    map.to_csv("analysis/choropleth/choropleth_statistics_de.csv", index=False)

def choropleth_ch():
    get_station_delay_ch = """
        SELECT
            bpuic AS trainstation,
            EXTRACT(EPOCH FROM AVG(predicted_arrival - arrival_time)) / 60 AS delay,
            COUNT(*) AS entries
        FROM swiss_trainstop
            WHERE predicted_arrival IS NOT NULL
            AND arrival_time IS NOT NULL
            AND cancellation_flag = false
            AND pass_through_flag = false
        GROUP BY bpuic;
    """

    get_station_cancellation_ch = """
        Select 
            bpuic As trainstation,
            SUM(Case When cancellation_flag = True Then 1 Else 0 End) as canceled,
            SUM(Case When cancellation_flag = False Then 1 Else 0 End) as not_canceled
        From swiss_trainstop
        Where pass_through_flag = false
            AND cancellation_flag Is Not Null
        Group By trainstation
    """
    
    station_delay_ch = pd.read_sql_query(get_station_delay_ch, conn)
    station_delay_ch.loc[station_delay_ch["delay"] < -1000, "delay"] += 1440
    station_delay_ch["delay"] = station_delay_ch["delay"].clip(lower=0)
    station_delay_ch["trainstation"] = station_delay_ch["trainstation"].astype(str)

    station_canceled_ch = pd.read_sql_query(get_station_cancellation_ch, conn)
    station_canceled_ch["trainstation"] = station_canceled_ch["trainstation"].astype("str")

    station_to_canton = pd.read_csv(
        "choropleth_ch.csv",
        dtype={"trainstation": "string", "id": "string"},
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    map = (
        station_delay_ch
        .merge(station_canceled_ch, on="trainstation", how="inner")
        .merge(station_to_canton, on="trainstation", how="inner")
    )

    map["delay"] = map["delay"] * map["entries"]

    map = (
        map
        .groupby("id", as_index=False)
        .agg(
            average_delay=("delay", "sum"),
            canceled=("canceled", "sum"),
            not_canceled=("not_canceled", "sum"),
            train_stops=("entries", "sum"),
            canton=("NAME", "first")
            )
    )

    map["average_delay"] = map["average_delay"] / map["train_stops"]
    map["canceled"] = 100 * map["canceled"] / (map["canceled"] + map["not_canceled"])

    shape_ch = gpd.read_file("analysis\ch\swissBOUNDARIES3D_1_5_TLM_KANTONSGEBIET.shp")

    shape_ch = shape_ch.merge(
        map,
        left_on="UUID",
        right_on="id",
        how="left"
    )

    _, ax = plt.subplots(figsize=(5.76, 3.67))

    shape_ch.plot(
        column="average_delay",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        # norm = colors.PowerNorm(gamma=0.3, vmin=shape_ch["average_delay"].min(), vmax=shape_ch["average_delay"].max()),
        missing_kwds={
            "color": "darkgrey",
            "label": "No data"
        },
        ax=ax
    )

    ax.set_title("Average Train Delay (minutes)")
    ax.axis("off")

    plt.savefig("analysis/choropleth/avg_delay_ch.png", dpi=512)
    plt.savefig("analysis/choropleth/avg_delay_ch.svg")

    plt.close()
    _, ax = plt.subplots(figsize=(5.76, 3.67))

    shape_ch.plot(
        column="train_stops",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        missing_kwds={
            "color": "darkgrey",
            "label": "No data"
        },
        ax=ax,   
    )
    
    ax.set_title("Total Train Stops")
    ax.axis("off")

    plt.savefig("analysis/choropleth/tot_stops_ch.png", dpi=512)
    plt.savefig("analysis/choropleth/tot_stops_ch.svg")

    plt.close()
    _, ax = plt.subplots(figsize=(5.76, 3.67))

    shape_ch.plot(
        column="canceled",
        cmap="RdYlGn_r",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        missing_kwds={
            "color": "darkgrey",
            "label": "No data"
        },
        ax=ax,   
    )
    
    ax.set_title("Average Train Cancelation (percentage)")
    ax.axis("off")

    plt.savefig("analysis/choropleth/avg_canceled_ch.png", dpi=512)
    plt.savefig("analysis/choropleth/avg_canceled_ch.svg")

    plt.close()

    map = map.rename(columns={"canceled": "average_cancelation"})

    map = map[["canton", "average_cancelation", "average_delay", "train_stops"]]
    map.to_csv("analysis/choropleth/choropleth_statistics_ch.csv", index=False)

if __name__ == "__main__":
    # Connection settings
    conn = psycopg2.connect(
        dbname="group-05",
        user="postgres",
        password="dbsys2025",
        host="localhost",
        port=5432
    )

    
    plt.rcParams.update({'font.size': 10})

    cur = conn.cursor()
    choropleth_de()
    choropleth_ch()

    conn.close()
    