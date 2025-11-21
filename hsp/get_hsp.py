import os
import json
import requests
import base64
from dotenv import load_dotenv
import csv
from multiprocessing import Pool, Manager, Semaphore
import time
import numpy as np

load_dotenv()

metrics_url = 'https://hsp-prod.rockshore.net/api/v1/serviceMetrics'
details_url = 'https://hsp-prod.rockshore.net/api/v1/serviceDetails'

username = os.environ["HSP_USERNAME"]
password = os.environ["HSP_PASSWORD"]

credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

headers = {
    'Authorization': f'Basic {credentials}',
    'Content-Type': 'application/json'
}

from_date = '2024-09-02'  # YYYY-MM-DD
to_date = '2024-09-12'

# Read CRS codes from CSV
crs_list = []

with open('trainlines-10.csv', 'r', newline='') as file:
    reader = csv.DictReader(file)
    for row in reader:
        crs_list.append((row["start"], row["end"]))

rid_folder_path = "train_rids"
details_folder_path = 'train_details'

os.makedirs(rid_folder_path, exist_ok=True)
os.makedirs(details_folder_path, exist_ok=True)

# Worker function for fetching service metrics
def get_hsp_data(task):
    from_crs, to_crs, from_time, to_time, weekday = task
    #time.sleep(np.random.uniform(0.5, 1.5))

    all_failed_rids = []
    all_failed_details = []

    print('working on', from_crs, to_crs, from_time, to_time, weekday)
    payload = {
        'from_loc': from_crs,
        'to_loc': to_crs,
        'from_time': from_time,
        'to_time': to_time,
        'from_date': from_date,
        'to_date': to_date,
        'days': weekday
    }

    rid_list = []
    attempt = 1

    while True:
        try:
            with request_rights:
                response = requests.post(metrics_url, json=payload, headers=headers)
                print(response.status_code)

            if response.ok:
                rid_json = response.json()

                for service in rid_json.get("Services", []):
                    rids = service.get("serviceAttributesMetrics", {}).get("rids", [])
                    rid_list += rids

                if len(rid_list) > 0:
                    file_path = os.path.join(rid_folder_path, f'rid_{from_crs}_{to_crs}_{from_time}_{to_time}_{weekday}.json')
                    with open(file_path, 'w') as f1:
                        json.dump(rid_json, f1, indent=2)

                    combined = []

                    for rid in rid_list:
                        details_json, failed_details = get_train_details(rid)
                        all_failed_details += failed_details
                        if details_json:
                            combined.append(details_json)
                    
                    file_path = os.path.join(details_folder_path, f'details_{from_crs}_{to_crs}_{from_time}_{to_time}_{weekday}.json')
                    with open(file_path, 'w') as f2:
                        json.dump(combined, f2, indent=2)
                
                print('done with', from_crs, to_crs, from_time, to_time, weekday)
                break
            elif response.status_code == 503:
                time.sleep(np.random.uniform(1.8, 2.2)*attempt)
            else:
                all_failed_rids.append([from_crs, to_crs, weekday])
                break
            
            attempt += 1

        except requests.exceptions.RequestException:
            all_failed_rids.append([from_crs, to_crs, weekday])
            break

    print(all_failed_rids, all_failed_details)
    return all_failed_rids, all_failed_details

# Worker function for fetching service details
def get_train_details(rid):
    details_json = None
    failed_local = []

    try:
        with request_rights:
            response = requests.post(details_url, json={'rid': rid}, headers=headers)

        if response.ok:
            details_json = response.json()
        else:
            failed_local.append([rid])
    except requests.exceptions.RequestException:
        failed_local.append([rid])
    
    return details_json, failed_local

def init_worker(shared_semaphore):
    global request_rights
    request_rights = shared_semaphore

if __name__ == '__main__':
    print(from_date, to_date)

    times = [("0000", "0759"), ("0800", "1559"), ("1600", "2359")]
    weekdays = ['WEEKDAY', 'SATURDAY', 'SUNDAY']

    tasks = []
    for crs in crs_list:
        from_crs, to_crs = crs
        for from_time, to_time in times:
            for weekday in weekdays:
                tasks.append((from_crs, to_crs, from_time, to_time, weekday))
                tasks.append((to_crs, from_crs, from_time, to_time, weekday))

    """ for task in tasks:
        failed_rid = get_hsp_data(task) """

    manager = Manager()
    failed_rid = manager.list()
    failed_details = manager.list()
    request_rights = manager.Semaphore(4)

    failed_rid.append(['from', 'to', 'day'])
    failed_details.append(['rid'])

    with Pool(initializer=init_worker, initargs=(request_rights,)) as pool:
        results = pool.map(get_hsp_data, tasks)

    rid_failed_local, details_failed_local = zip(*results)

    for r in rid_failed_local:
        failed_rid.extend(r)

    for r in details_failed_local:
        failed_details.extend(r)

    with open("failed_rid.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(failed_rid)

    with open("failed_details.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(failed_details)
