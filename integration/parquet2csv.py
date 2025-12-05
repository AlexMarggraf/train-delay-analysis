import pandas as pd
import glob
import os

# For all german train parquet files
for file in glob.glob(r"Deutschland/DB/monthly_processed_data/*.parquet"):
    name = os.path.splitext(file)[0]

    # Load parquet file into dataframe
    df = pd.read_parquet(file)

    # Assign correct datatype
    df["eva"] = df["eva"].astype("string")
    df["train_line_ride_id"] = df["train_line_ride_id"].astype("string")

    # Store file as csv
    df.to_csv(f"./{name}.csv", index=False)