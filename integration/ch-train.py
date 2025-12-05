import pandas as pd
import json
import glob
import os
from datetime import datetime
from pathlib import Path

def separate_data(file, dest_folder, date):
    # Load data file into dataframe
    df_master = pd.read_csv(
        file,
        sep=';',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Load already exisitng swiss trainstations into a dataframe
    df_trainstation = pd.read_csv(
        r"swiss_trainstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Load already existing swiss operators into a dataframe
    df_operator = pd.read_csv(
        r"swiss_operator.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Keep only trains
    df_master = df_master[df_master['PRODUKT_ID'] == 'Zug']

    # Required columns to keep a row at all
    required_columns = [
        "BETREIBER_ID",
        "HALTESTELLEN_NAME",
        "BPUIC",
        "LINIEN_ID",
        "BETRIEBSTAG",
        "FAHRT_BEZEICHNER"
    ]

    # Normalize empty to NA
    df_master[required_columns] = df_master[required_columns].replace(
        r'^\s*$', pd.NA, regex=True
    )

    # Remove rows with missing required fields
    df_master = df_master.dropna(subset=required_columns)

    # Load the last id value
    with open("id_counters.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Get safely, probably unessecary lol
    counter = data.get("stop", 0)

    # Columns of swiss trainstation
    trainstation = (
        df_master[["BPUIC", "HALTESTELLEN_NAME"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Concatenate already exisitng trainstations with new trainstations and drop duplicates
    trainstation = pd.concat([trainstation, df_trainstation], axis=0)
    trainstation.drop_duplicates(inplace=True)

    # Safe dataframe in file
    trainstation.to_csv("swiss_trainstation.csv", index=False)

    # Columns of swiss operator
    operator = (
        df_master[["BETREIBER_ID", "BETREIBER_ABK", "BETREIBER_NAME"]]
        .drop_duplicates()
    )

    # Concatenate already exisitng operators with new operators and drop dublicates
    operator = pd.concat([operator, df_operator], axis=0)
    operator.drop_duplicates(inplace=True)

    # Save dataframe as file
    operator.to_csv("swiss_operator.csv", index=False)

    # Columns of swiss trainline dataframe
    line = (
        df_master[["LINIEN_ID", "FAHRT_BEZEICHNER", "BETRIEBSTAG", 
                   "BETREIBER_ID", "LINIEN_TEXT", "VERKEHRSMITTEL_TEXT",
                   "PRODUKT_ID", "UMLAUF_ID"
                    ]]
        .drop_duplicates()
    )

    # Format date
    line["BETRIEBSTAG"] = pd.to_datetime(line["BETRIEBSTAG"], format="%d.%m.%Y", errors="coerce").dt.strftime("%Y-%m-%d").fillna("")

    # Store dataframe in csv
    line.to_csv(f"{dest_folder}/line-{date}.csv", index=False)

    # Columns of swiss trainstop dataframe
    stop = (
        df_master[[
                "BPUIC", "LINIEN_ID", "FAHRT_BEZEICHNER",
                "BETRIEBSTAG", "ANKUNFTSZEIT", "ABFAHRTSZEIT",
                "AN_PROGNOSE", "AB_PROGNOSE", "AN_PROGNOSE_STATUS",
                "AB_PROGNOSE_STATUS", "DURCHFAHRT_TF", "FAELLT_AUS_TF",
                "ZUSATZFAHRT_TF"
            ]]
        .drop_duplicates()
    )

    timestamps_1 = ["ANKUNFTSZEIT", "ABFAHRTSZEIT"]
    timestamps_2 = ["AN_PROGNOSE", "AB_PROGNOSE"]

    # Format date
    for col in timestamps_1:
        stop[col] = pd.to_datetime(stop[col], format="%d.%m.%Y %H:%M", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
    
    for col in timestamps_2:
        stop[col] = pd.to_datetime(stop[col], format="%d.%m.%Y %H:%M:%S", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    stop["BETRIEBSTAG"] = pd.to_datetime(stop["BETRIEBSTAG"], format="%d.%m.%Y", errors="coerce").dt.strftime("%Y-%m-%d").fillna("")

    # Generate new stop_id
    stop["stop_id"] = range(counter, counter + len(stop))

    # Reorder
    stop = stop[[
        "stop_id", "BPUIC", "LINIEN_ID",
        "FAHRT_BEZEICHNER", "BETRIEBSTAG", "ANKUNFTSZEIT",
        "ABFAHRTSZEIT", "AN_PROGNOSE", "AB_PROGNOSE",
        "AN_PROGNOSE_STATUS", "AB_PROGNOSE_STATUS", "DURCHFAHRT_TF",
        "FAELLT_AUS_TF", "ZUSATZFAHRT_TF"
    ]]
    
    # Increase counter and store
    counter += len(stop)
    with open("id_counters.json", "w") as f:
        json.dump({"stop": counter}, f)

    # Store dataframe in file
    stop.to_csv(f"{dest_folder}/stop-{date}.csv", index=False)

    print("✓ All tables successfully generated")

if __name__ == "__main__":
    # Generate files
    data = {
        "stop": 0
    }

    with open("id_counters.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    operator_columns = ["BETREIBER_ID", "BETREIBER_ABK", "BETREIBER_NAME"]

    operator_df = pd.DataFrame(columns=operator_columns)
    operator_df.to_csv("swiss_operator.csv", index=False, encoding="utf-8")

    trainstation_columns = ["HALTESTELLEN_NAME", "BPUIC"]

    trainstation_df = pd.DataFrame(columns=trainstation_columns)
    trainstation_df.to_csv("swiss_trainstation.csv", index=False, encoding="utf-8")

    # For all sbb data files
    for file in glob.glob(r"Schweiz\SBB\**\*.csv", recursive=True):
        print("Processing:", file)

        filepath = Path(file)
        date = filepath.stem.split("_")[0]

        date_obj = datetime.strptime(date, "%Y-%m-%d")
        folder_tail = f"{date_obj.year}-{date_obj.month}"

        dest_folder = f"processed\sbb\{folder_tail}"
        os.makedirs(dest_folder, exist_ok=True)

        # Clean data
        separate_data(file, dest_folder, date)

    # Load swiss trainstations into dataframe
    ts_final = pd.read_csv(
        r"swiss_trainstation.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Load swiss operators into dataframe
    op_final = pd.read_csv(
        r"swiss_operator.csv",
        sep=',',
        quotechar='"',
        on_bad_lines='skip',
        low_memory=False
    )

    # Drop dublicates and store. subset needed here, same station twice but does not get removed
    ts_final.drop_duplicates(subset=["BPUIC"], inplace=True)
    ts_final.to_csv("processed/sbb/swiss_trainstation.csv", index=False)

    # Drop dublicates
    op_final.drop_duplicates(inplace=True)

    # Remove faulty datapoint
    op_final = op_final[~((op_final['BETREIBER_ID'] == '81:810003') & (op_final['BETREIBER_ABK'] == 'A'))]
    
    # Store operator dataframe in file
    op_final.to_csv("processed/sbb/swiss_operator.csv", index=False)
