import psycopg2
import pandas as pd
from scipy.stats import mannwhitneyu
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import numpy as np
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
    "../report/analysis_results/delay_per_country.csv",
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

weather_summary.to_csv(
    "../report/analysis_results/weather_effect_summary.csv"
)

# ============================================================
# 6. STATISTICAL TESTS
# ============================================================

print("\n=== MANN–WHITNEY U TESTS ===")

mw_results = []

for c in ["DE", "CH"]:
    bad = df[(df.country_x == c) & (df.bad_weather == 1)]["delay_minutes"]
    normal = df[(df.country_x == c) & (df.bad_weather == 0)]["delay_minutes"]

    if len(bad) > 0 and len(normal) > 0:
        stat, p = mannwhitneyu(bad, normal, alternative="greater")
        mw_results.append({
            "country": c,
            "u_statistic": stat,
            "p_value": p,
            "n_bad_weather": len(bad),
            "n_normal_weather": len(normal)
        })
    else:
        mw_results.append({
            "country": c,
            "u_statistic": np.nan,
            "p_value": np.nan,
            "n_bad_weather": len(bad),
            "n_normal_weather": len(normal)
        })

mw_df = pd.DataFrame(mw_results)

print(mw_df)

mw_df.to_csv(
    "../report/analysis_results/mann_whitney_weather_effect.csv",
    index=False
)

# ============================================================
# 7. REGRESSION MODEL Note: Switzerland is baseline, that's why there is no country_CH in the result
# ============================================================

print("\n=== REGRESSION MODEL ===")

reg = smf.ols(
    "delay_minutes ~ precipitation + temperature + wind_speed "
    "+ country_DE + precipitation:country_DE",
    data=df
).fit(cov_type="HC3")

print(reg.summary())

reg_summary = pd.DataFrame({
    "coefficient": reg.params,
    "std_error": reg.bse,
    "t_value": reg.tvalues,
    "p_value": reg.pvalues
})

reg_summary.to_csv(
    "../report/analysis_results/regression_results.csv"
)

# Helper function for 95% confidence interval

def mean_ci(series, z=1.96):
  mean = series.mean()
  std = series.std()
  n = series.count()

  if n == 0:
    return pd.Series([np.nan, np.nan, np.nan])

  half_width = z * std / np.sqrt(n)
  return pd.Series([mean, mean - half_width, mean + half_width])

def prepare_plot_data(df, category_col, country_col="country_x"):
    categories = df[category_col].dropna().unique()
    categories = sorted(categories, key=str)

    plot_data = {}
    for country in ["DE", "CH"]:
        sub = (
            df[df[country_col] == country]
            .set_index(category_col)
            .reindex(categories)
        )
        plot_data[country] = sub

    return categories, plot_data


COLOR_CH = "#1f77b4"  # blue
COLOR_DE = "#ff7f0e"  # orange

COUNTRY_COLORS = {
    "Germany": COLOR_DE,
    "Switzerland": COLOR_CH
}

# ============================================================
# 8. DELAY PER WEATHER (PRECIPITATION BINS, DE vs CH)
# ============================================================
# Derive weather type from precipitation and temperature
def classify_weather(row):
    if row["precipitation"] > 0 and row["temperature"] <= 0:
        return "Snow"
    elif row["precipitation"] >= 10:
        return "Heavy rain"
    elif row["precipitation"] >= 5:
        return "Rain"
    elif row["precipitation"] > 0:
        return "Light rain"
    else:
        return "Dry"

df["weather_type"] = df.apply(classify_weather, axis=1)

weather_stats = (
    df.groupby(["weather_type", "country_x"])["delay_minutes"]
      .apply(mean_ci)
      .unstack()
)

weather_stats.columns = ["mean_delay", "ci_lower", "ci_upper"]
weather_stats = weather_stats.reset_index()

weather_stats.to_csv(
    "../report/analysis_results/delay_per_weather.csv",
    index=False
)

# Bar chart
fig, ax = plt.subplots(figsize=(10, 6))

weather_types, plot_data = prepare_plot_data(
    weather_stats, "weather_type"
)

x = np.arange(len(weather_types))
width = 0.35

for i, country in enumerate(["CH", "DE"]):
    sub = plot_data[country]

    means = sub["mean_delay"].values
    yerr = [
        means - sub["ci_lower"].values,
        sub["ci_upper"].values - means
    ]

    if country == "CH":
        country = ("Switzerland")
    else:
        country = ("Germany")

    ax.bar(
        x + i * width,
        means,
        width,
        yerr=yerr,
        capsize=4,
        color=COUNTRY_COLORS[country],
        label=country
    )

ax.set_xticks(x + width / 2)
ax.set_xticklabels(weather_types, rotation=30)
ax.set_ylabel("Mean delay (minutes)")
ax.set_title("Mean train delay by weather type")
ax.legend(title="Country")

plt.tight_layout()
plt.savefig("../report/analysis_results/delay_per_weather.png", dpi=300)
plt.show()

# ============================================================
# 9 DELAY PER PRECIPITATION (PRECIPITATION BINS SIZE 5, DE vs CH)
# ============================================================

# Create precipitation bins of size 5 mm
max_precip = df["precipitation"].max()
bins = list(range(0, int(max_precip // 5 * 5 + 10), 5))

df["precip_bin"] = pd.cut(
    df["precipitation"],
    bins=bins,
    right=False,
    include_lowest=True
)

weather_bin_stats = (
    df.groupby(["precip_bin", "country_x"])["delay_minutes"]
      .apply(mean_ci)
      .unstack()
)

weather_bin_stats.columns = ["mean_delay", "ci_lower", "ci_upper"]
weather_bin_stats = weather_bin_stats.reset_index()

weather_bin_stats.to_csv(
    "../report/analysis_results/delay_per_precipitation.csv",
    index=False
)

# ------------------------------------------------------------
# Bar chart
# ------------------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 6))

bins = weather_bin_stats["precip_bin"].cat.categories
x = np.arange(len(bins))
width = 0.35

for i, country in enumerate(["CH", "DE"]):
    sub = (
        weather_bin_stats[weather_bin_stats["country_x"] == country]
        .set_index("precip_bin")
        .reindex(bins)
    )

    means = sub["mean_delay"].values
    yerr = [
        means - sub["ci_lower"].values,
        sub["ci_upper"].values - means
    ]

    if country == "CH":
        country = ("Switzerland")
    else:
        country = ("Germany")

    ax.bar(
        x + i * width,
        means,
        width,
        yerr=yerr,
        capsize=4,
        color=COUNTRY_COLORS[country],
        label=country
    )

ax.set_xticks(x + width / 2)
ax.set_xticklabels([str(b) for b in bins], rotation=45)
ax.set_xlabel("Precipitation (mm)")
ax.set_ylabel("Mean delay (minutes)")
ax.set_title("Mean train delay by precipitation")
ax.legend(title="Country")

plt.tight_layout()
plt.savefig("../report/analysis_results/delay_per_precipitation.png", dpi=300)
plt.show()

# ============================================================
# 10. DELAY PER MONTH (DE vs CH)
# ============================================================

# Derive month from timestamp
df["month_num"] = df["hour"].dt.month
df["month_name"] = df["hour"].dt.strftime("%B")

monthly_stats = (
    df.groupby(["month_num", "month_name", "country_x"])["delay_minutes"]
      .apply(mean_ci)
      .unstack()
)

monthly_stats.columns = ["mean_delay", "ci_lower", "ci_upper"]
monthly_stats = (
    monthly_stats
    .reset_index()
    .sort_values("month_num")
)

monthly_stats.to_csv(
    "../report/analysis_results/delay_per_month.csv",
    index=False
)

# Bar chart
fig, ax = plt.subplots(figsize=(12, 6))

months, plot_data = prepare_plot_data(
    monthly_stats, "month_name"
)

x = np.arange(len(months))
width = 0.35

for i, country in enumerate(["CH", "DE"]):
    sub = plot_data[country]

    means = sub["mean_delay"].values
    yerr = [
        means - sub["ci_lower"].values,
        sub["ci_upper"].values - means
    ]

    if country == "CH":
        country = ("Switzerland")
    else:
        country = ("Germany")

    ax.bar(
        x + i * width,
        means,
        width,
        yerr=yerr,
        capsize=4,
        color=COUNTRY_COLORS[country],
        label=country
    )

ax.set_xticks(x + width / 2)
ax.set_xticklabels(months, rotation=45)
ax.set_ylabel("Mean delay (minutes)")
ax.set_title("Mean train delay by month")
ax.legend(title="Country")

plt.tight_layout()
plt.savefig("../report/analysis_results/delay_per_month.png", dpi=300)
plt.show()