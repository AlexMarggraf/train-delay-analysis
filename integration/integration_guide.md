# Integration Process of Group-05

---

## Downloading data

- [Raw data](https://1drv.ms/f/c/17ccd6bf5a936617/EkbsqmAe1xBPiYO1JJ-rjcoBaVXuVk_GOr-c0bRsYoRqmw?e=52AnHz
) (Download Data.zip)
- [Swiss weatherstation metadata](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv)
- [Python scripts / SQL create file](https://git.scicore.unibas.ch/dbis/lecture-groups/database-systems/2025hs/group-05)

---

## Setting up the workspace

Extract the Data.zip folder and additionally all zip folders inside Data. Now Set your Data folder up like shown below and remove:

- `Deutschland/DB/raw_data`
- **data-2024-07.parquet**, **data-2024-08.parquet**, **data-2025-09.parquet** and **data-2025-10.parquet** from `Deutschland/DB/monthly_processed_data/`
- `Schweiz/SBB/ist-daten-2025-09`
- `Schweiz/SBB/ist-daten-2025-10`

```
Data
├── Deutschland
│   ├── DB
│   │   └── monthly_processed_data
│   └── DWD
│       └── dwd_filtered
│           ├── air_temperature
│           │   ├── historical
│           │   └── recent
│           ├── precipitation
│           │   ├── historical
│           │   └── recent
│           ├── pressure
│           │   ├── historical
│           │   └── recent
│           └── wind
│               ├── historical
│               └── recent
├── Schweiz
│   ├── MeteoCH
│   │   ├── output_historical_2020_2029
│   │   └── output_recent_2025
│   └── SBB
│       ├── ist-daten-2024-09
│       ├── ...
│       └── ist_daten-2025-08
```

Furthermore place the following python scripts in the Data folder.

For cleaning:

- **parquet2csv.py**
- **ch-train.py**
- **ch-weather.py**
- **de-train.py**
- **de-weather.py**

For integrating:

- **integrate_db.py**
- **integrate_dwd.py**
- **integrate_meteoSwiss.py**
- **integrate_sbb.py**

---

## Software requirements

You will need:

- Python version 3.12
- Packages:
    - Pandas
    - json
    - glob
    - os
    - datetime
    - pathlib
    - numpy
    - psycopg2
- PostgreSQL version 16.11
- pgAdmin 4

## Data integration

To clean your data run the following files. Make sure to run **parquet2csv.py** before you run **de-train.py**.

- **parquet2csv.py**
- **ch-train.py**
- **ch-weather.py**
- **de-train.py**
- **de-weather.py**

To integrate your data, first create a new postgreSQL database localy called **group-05** with password **dbsys2025**. Then run the file **create.sql** inside pgAdmin 4 to create all Tables and index structures.

After that place the swiss weatherstation metadata file in the folder `processed/meteoSwiss` and run the following files in any order:

- **integrate_db.py**
- **integrate_dwd.py**
- **integrate_meteoSwiss.py**
- **integrate_sbb.py**