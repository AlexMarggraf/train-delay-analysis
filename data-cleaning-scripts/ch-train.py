import pandas as pd
import json
import glob
import os
from datetime import datetime
from pathlib import Path

def separate_data(file, dest_folder, date):
    # -----------------------------
    # 1. LOAD CSV AND FILTER
    # -----------------------------
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    df_trainstation = pd.read_csv(
        r"swiss_trainstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    df_operator = pd.read_csv(
        r"operator.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Keep only trains
    df_master = df_master[df_master['PRODUKT_ID'] == 'Zug']

    # Required columns to keep a row at all
    required_columns = [
        "ANKUNFTSZEIT", "ABFAHRTSZEIT",
        "AN_PROGNOSE", "AB_PROGNOSE",
        "BPUIC", "BETREIBER_ID",
        "HALTESTELLEN_NAME", "LINIEN_ID"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns)

    # use this to check the cleaned dataframe
    # df_master.to_csv("control_cleaned.csv", index=False)
    # print("✓ Cleaned master saved as control_cleaned.csv")
    # print(df_master[required_columns].isna().sum())


    # ---------------------------------------------------------
    # 2. TABLE GENERATION — CLEAN, DEDUPED, RELATIONAL STRUCTURE
    # ---------------------------------------------------------

    with open("id_counters.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    counter = data.get("stop", 0)

    # -----------------------------
    # Table: Trainstation
    # -----------------------------
    trainstation = (
        df_master[["HALTESTELLEN_NAME", "BPUIC"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    trainstation = pd.concat([trainstation, df_trainstation], axis=0)
    trainstation.drop_duplicates(inplace=True)
    trainstation.to_csv("swiss_trainstation.csv", index=False)

    # print("✓ Saved Trainstation.csv")

    # -----------------------------
    # Table: Operator
    # -----------------------------
    operator = (
        df_master[["BETREIBER_ID", "BETREIBER_ABK", "BETREIBER_NAME"]]
        .drop_duplicates()
    )
    operator = pd.concat([operator, df_operator], axis=0)
    operator.drop_duplicates(inplace=True)
    operator.to_csv("operator.csv", index=False)
    # print("✓ Saved Operator.csv")


    # -----------------------------
    # Table: Line
    # -----------------------------
    line = (
        df_master[["LINIEN_ID", "LINIEN_TEXT", "PRODUKT_ID",
                    "UMLAUF_ID", "VERKEHRSMITTEL_TEXT",
                    "FAHRT_BEZEICHNER", "BETREIBER_ID",
                "BETRIEBSTAG"]]
        .drop_duplicates()
    )
    line.to_csv(f"{dest_folder}/line-{date}.csv", index=False)
    # print("✓ Saved Line.csv")


    # -----------------------------
    # Table: Stop (base type)
    # -----------------------------
    stop = (
        df_master[
            [
                "HALTESTELLEN_NAME",
                "ANKUNFTSZEIT", "ABFAHRTSZEIT",
                "AN_PROGNOSE", "AB_PROGNOSE",
                "AN_PROGNOSE_STATUS", "AB_PROGNOSE_STATUS",
                "DURCHFAHRT_TF", "LINIEN_ID",
                "FAELLT_AUS_TF", "ZUSATZFAHRT_TF"
            ]
        ]
        .drop_duplicates()
    )

    # Generate new stop_id AFTER deduplication
    stop["stop_id"] = range(counter, counter + len(stop))
    counter += len(stop)

    stop.to_csv(f"{dest_folder}/stop-{date}.csv", index=False)
    # print("✓ Saved Stop.csv")


    # -----------------------------
    # Save ID counters (if needed)
    # -----------------------------
    with open("id_counters.json", "w") as f:
        json.dump({"stop": counter}, f)

    print("✓ All tables successfully generated")

if __name__ == "__main__":

    data = {
        "stop": 0
    }

    with open("id_counters.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    operator_columns = ["BETREIBER_ID", "BETREIBER_ABK", "BETREIBER_NAME"]

    operator_df = pd.DataFrame(columns=operator_columns)
    operator_df.to_csv("operator.csv", index=False, encoding="utf-8")

    trainstation_columns = ["HALTESTELLEN_NAME", "BPUIC"]

    trainstation_df = pd.DataFrame(columns=trainstation_columns)
    trainstation_df.to_csv("swiss_trainstation.csv", index=False, encoding="utf-8")


    for file in glob.glob(r"Schweiz\SBB\**\*.csv", recursive=True):
        print("Processing:", file)

        filepath = Path(file)
        date = filepath.stem.split("_")[0]

        date_obj = datetime.strptime(date, "%Y-%m-%d")
        folder_tail = f"{date_obj.year}-{date_obj.month}"

        dest_folder = f"Schweiz\processed\{folder_tail}"
        os.makedirs(dest_folder, exist_ok=True)

        separate_data(file, dest_folder, date)
