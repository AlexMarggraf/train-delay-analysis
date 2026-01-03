import psycopg2
import pandas as pd
from scipy.stats import mannwhitneyu
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path

# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = psycopg2.connect(
    dbname="group-05",
    user="postgres",
    password="dbsys2025",
    host="localhost",
    port=5432
)

# ============================================================
# 1. LOAD DATA (NO LOGIC IN SQL)
# ============================================================

sql_train_de = """
SELECT
    eva AS trainstation,
    arrival_planned_time AS timestamp,
    delay_in_min
FROM german_trainstop
WHERE delay_in_min IS NOT NULL
  AND arrival_planned_time IS NOT NULL
  AND is_canceled = false;
"""

sql_train_ch = """
SELECT
    bpuic AS trainstation,
    arrival_time AS timestamp,
    predicted_arrival
FROM swiss_trainstop
WHERE predicted_arrival IS NOT NULL
  AND arrival_time IS NOT NULL
  AND cancellation_flag = false
  AND pass_through_flag = false;
"""

sql_weather_de = """
SELECT
    station_id AS weatherstation,
    station_timestamp AS timestamp,
    precipitation_mm AS precipitation,
    temperature_c AS temperature,
    wind_speed
FROM german_prec
JOIN german_temp USING (station_id, station_timestamp)
JOIN german_wind USING (station_id, station_timestamp);
"""

sql_weather_ch = """
SELECT
    station_abbr AS weatherstation,
    station_timestamp AS timestamp,
    precipitation,
    temp_2m_mean AS temperature,
    wind_speed_10m_mean AS wind_speed
FROM swiss_measurement;
"""

sql_mapping = """
SELECT
    trainstation,
    trainstation_in_ch,
    weatherstation
FROM trainstation_weatherstation;
"""

df_train_de = pd.read_sql_query(sql_train_de, conn)
df_train_ch = pd.read_sql_query(sql_train_ch, conn)
df_weather_de = pd.read_sql_query(sql_weather_de, conn)
df_weather_ch = pd.read_sql_query(sql_weather_ch, conn)
df_map = pd.read_sql_query(sql_mapping, conn)

conn.close()
print("✔ Data loaded")

# ============================================================
# 2. PREPROCESSING
# ============================================================

# Swiss delay calculation
df_train_ch["delay_minutes"] = (
    (df_train_ch["predicted_arrival"] - df_train_ch["timestamp"])
    .dt.total_seconds() / 60
)

# Standardize train data
df_train_de["delay_minutes"] = df_train_de["delay_in_min"]
df_train_de["country"] = "DE"
df_train_ch["country"] = "CH"

df_train = pd.concat([
    df_train_de[["trainstation", "timestamp", "delay_minutes", "country"]],
    df_train_ch[["trainstation", "timestamp", "delay_minutes", "country"]]
])

# Standardize weather data
df_weather_de["country"] = "DE"
df_weather_ch["country"] = "CH"

df_weather = pd.concat([
    df_weather_de[["weatherstation", "timestamp", "precipitation", "temperature", "wind_speed", "country"]],
    df_weather_ch[["weatherstation", "timestamp", "precipitation", "temperature", "wind_speed", "country"]]
])

# Ensure datetime
df_train["timestamp"] = pd.to_datetime(df_train["timestamp"])
df_weather["timestamp"] = pd.to_datetime(df_weather["timestamp"])

# Create hourly timestamps
df_train["hour"] = df_train["timestamp"].dt.floor("H")
df_weather["hour"] = df_weather["timestamp"].dt.floor("H")

# ============================================================
# 3. COUNTRY-SPECIFIC MERGING (KEY FIX)
# ============================================================

# --- Germany ---
df_map_de = df_map[df_map["trainstation_in_ch"] == False]

#print('df map de', df_map_de)

df_train_de = df_train.merge(
    df_map_de, on="trainstation", how="inner"
)

df_train_de["country"] = "DE"

#print('df train de', df_train_de)

df_weather_de = df_weather[df_weather.country == "DE"]
df_weather_de["weatherstation"] = df_weather_de["weatherstation"].astype('str')

#print('df weather de', df_weather_de)

df_de = df_train_de.merge(
    df_weather_de,
    on=["weatherstation", "hour"],
    how="inner"
)

#print('df de', df_de)

# --- Switzerland ---
df_map_ch = df_map[df_map["trainstation_in_ch"] == True]

#print(df_map_ch)

df_train["trainstation"] = df_train["trainstation"].astype(str)

df_train_ch = df_train.merge(
    df_map_ch, on="trainstation", how="inner"
)

#print(df_train_ch)

df_train_ch["country"] = "CH"

df_weather_ch = df_weather[df_weather.country == "CH"]

#print(df_weather_ch)

df_ch = df_train_ch.merge(
    df_weather_ch,
    on=["weatherstation", "hour"],
    how="inner"
)

#print(df_ch)

# Combine
df = pd.concat([df_de, df_ch])
print("✔ Final merged dataset size:", len(df))

if len(df) == 0:
    raise RuntimeError(
        "No train–weather matches found. "
        "Station mapping or timestamps do not align."
    )

# ============================================================
# 4. BASELINE DELAYS
# ============================================================

print("\n=== BASELINE DELAYS ===")
print(
    df_de.groupby("country_x")["delay_minutes"]
    .agg(["mean", "median", "count"])
)

print(
    df_ch.groupby("country_x")["delay_minutes"]
    .agg(["mean", "median", "count"])
)

# ============================================================
# 4a. DELAY PER COUNTRY – TABLE
# ============================================================

country_stats = (
    df.groupby("country_x")["delay_minutes"]
      .agg(
          mean_delay="mean",
          median_delay="median",
          std_delay="std",
          count="count"
      )
      .reset_index()
)

print("\n=== DELAY PER COUNTRY (TABLE) ===")
print(country_stats)

# Optional: save for report
country_stats.to_csv(
    "../report/delay_per_country.csv",
    index=False
)



# ============================================================
# 5. WEATHER EFFECT
# ============================================================

df["bad_weather"] = (df["precipitation"] > 5).astype(int)
df["country_DE"] = (df["country_x"] == "DE").astype(int)

weather_summary = (
    df.groupby(["country_x", "bad_weather"])["delay_minutes"]
    .mean()
    .unstack()
    .rename(columns={0: "normal_weather", 1: "bad_weather"})
)

weather_summary["weather_effect"] = (
    weather_summary["bad_weather"]
    - weather_summary["normal_weather"]
)

print("\n=== WEATHER EFFECT (MEAN DELAYS) ===")
print(weather_summary)

# ============================================================
# 6. STATISTICAL TESTS
# ============================================================

print("\n=== MANN–WHITNEY U TESTS ===")

for c in ["DE", "CH"]:
    bad = df[(df.country_x == c) & (df.bad_weather == 1)]["delay_minutes"]
    normal = df[(df.country_x == c) & (df.bad_weather == 0)]["delay_minutes"]

    if len(bad) > 0 and len(normal) > 0:
        stat, p = mannwhitneyu(bad, normal, alternative="greater")
        print(f"{c}: p-value = {p:.6f}")
    else:
        print(f"{c}: insufficient data")

# ============================================================
# 7. REGRESSION MODEL
# ============================================================

print("\n=== REGRESSION MODEL ===")

reg = smf.ols(
    "delay_minutes ~ precipitation + temperature + wind_speed "
    "+ country_DE + precipitation:country_DE",
    data=df
).fit(cov_type="HC3")

print(reg.summary())

'''
# ============================================================
# 8. REGIONAL DELAYS (CHOROPLETH DATA)
# ============================================================

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"

# Choropleth CSVs are in project root
chor_de = pd.read_csv(BASE_DIR / "choropleth_de.csv")
chor_ch = pd.read_csv(BASE_DIR / "choropleth_ch.csv")

# Ensure consistent types for merge keys
df_de["trainstation"] = df_de["trainstation"].astype(str)
df_ch["trainstation"] = df_ch["trainstation"].astype(str)

chor_de["trainstation"] = chor_de["trainstation"].astype(str)
chor_ch["trainstation"] = chor_ch["trainstation"].astype(str)

print("\nLoaded choropleth CSVs")
print("DE CSV columns:", chor_de.columns.tolist())
print("CH CSV columns:", chor_ch.columns.tolist())

# ------------------------------------------------------------
# Load shapefiles
# ------------------------------------------------------------

gdf_de = gpd.read_file(
    ANALYSIS_DIR / "de" / "VG2500_KRS.shp"
)

gdf_ch = gpd.read_file(
    ANALYSIS_DIR / "ch" / "swissBOUNDARIES3D_1_5_TLM_KANTONSGEBIET.shp"
)

print("\nLoaded shapefiles")
print("DE shapefile columns:", gdf_de.columns.tolist())
print("CH shapefile columns:", gdf_ch.columns.tolist())

# ------------------------------------------------------------
# Germany: Mean delay per Landeskreis
# ------------------------------------------------------------

df_de_region = df_de.merge(
    chor_de,
    left_on="trainstation",
    right_on="id",
    how="inner"
)

de_region_stats = (
    df_de_region
    .groupby("NAME")["delay_minutes"]
    .mean()
    .reset_index()
    .rename(columns={
        "NAME": "landeskreis",
        "delay_minutes": "mean_delay"
    })
)

print("\n=== DELAY PER LANDESKREIS (DE) ===")
print(de_region_stats.head())

# Join with shapefile (GEN = Landkreis name)
gdf_de = gdf_de.merge(
    de_region_stats,
    left_on="GEN",
    right_on="landeskreis",
    how="left"
)

# ------------------------------------------------------------
# Switzerland: Mean delay per Kanton
# ------------------------------------------------------------

df_ch_region = df_ch.merge(
    chor_ch,
    left_on="trainstation",
    right_on="id",
    how="inner"
)

ch_region_stats = (
    df_ch_region
    .groupby("NAME")["delay_minutes"]
    .mean()
    .reset_index()
    .rename(columns={
        "NAME": "kanton",
        "delay_minutes": "mean_delay"
    })
)

print("\n=== DELAY PER KANTON (CH) ===")
print(ch_region_stats.head())

# Join with shapefile (NAME = Kanton name)
gdf_ch = gdf_ch.merge(
    ch_region_stats,
    left_on="NAME",
    right_on="kanton",
    how="left"
)

# ------------------------------------------------------------
# Save aggregated data
# ------------------------------------------------------------

de_region_stats.to_csv(
    BASE_DIR / "report" / "delay_per_landeskreis_de.csv",
    index=False
)

ch_region_stats.to_csv(
    BASE_DIR / "report" / "delay_per_kanton_ch.csv",
    index=False
)

print("\n✔ Regional delay datasets prepared for choropleth mapping")
'''


# ============================================================
# 9. DELAY PER WEATHER (DE vs CH) TODO Change percipitation to actual weather for future + save bar chart
# ============================================================

weather_type_stats = (
    df.groupby(["precipitation", "country_x"])["delay_minutes"]
      .mean()
      .unstack("country_x")
      .rename(columns={
          "DE": "mean_delay_DE",
          "CH": "mean_delay_CH"
      })
      .reset_index()
)

print("\n=== DELAY PER WEATHER (DE vs CH) ===")
print(weather_type_stats)

weather_type_stats.to_csv(
    "../report/delay_per_weather_type_de_ch.csv",
    index=False
)


# Bar Chart

weather_type_stats.set_index("precipitation").plot(
    kind="bar"
)

plt.ylabel("Mean delay (minutes)")
plt.title("Mean delay by weather (DE vs CH)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

'''
# ============================================================
# 10. DELAY PER MONTH (DE vs CH) TODO Month is not an attribute and needs to be derived from timestamps + save bar chart
# ============================================================

monthly_stats = (
    df.groupby(["month", "country_x"])["delay_minutes"]
      .mean()
      .unstack("country_x")
      .rename(columns={
          "DE": "mean_delay_DE",
          "CH": "mean_delay_CH"
      })
      .reset_index()
      .sort_values("month")
)

print("\n=== DELAY PER MONTH (DE vs CH) ===")
print(monthly_stats)

monthly_stats.to_csv(
    "../report/delay_per_month_de_ch.csv",
    index=False
)


# Bar Chart

monthly_stats.set_index("month").plot(
    kind="bar"
)

plt.xlabel("Month")
plt.ylabel("Mean delay (minutes)")
plt.title("Mean delay by month (DE vs CH)")
plt.xticks(range(0, 12), range(1, 13))
plt.tight_layout()
plt.show()
'''
