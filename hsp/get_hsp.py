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

from_date = '2024-09-01'  # YYYY-MM-DD
to_date = '2024-09-03'

crs_list = []

# get start and end points of all train lines, specify your file here
file_name = 'trainlines-alex.csv'
with open(file_name, 'r', newline='') as file:
    reader = csv.DictReader(file)
    for row in reader:
        crs_list.append((row["start"], row["end"]))

rid_folder_path = "train_rids"
details_folder_path = 'train_details'

# creates folders, delete them before running this script.
os.makedirs(rid_folder_path, exist_ok=True)
os.makedirs(details_folder_path, exist_ok=True)

def get_hsp_data(task):
    from_crs, to_crs, from_time, to_time, weekday = task

    all_failed_rids = []
    all_failed_details = []

    # leave this in to know your program is still working
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

    # try 5 times to request data from the api
    while attempt < 6:
        try:
            # get semaphore access
            with request_rights:
                # the actual https request
                response = requests.post(metrics_url, json=payload, headers=headers)
            # print(response.status_code)

            # if request worked out
            if response.ok:
                rid_json = response.json()

                # get all rids from the response
                for service in rid_json.get("Services", []):
                    rids = service.get("serviceAttributesMetrics", {}).get("rids", [])
                    rid_list += rids

                # store  the response in a json file
                if len(rid_list) > 0:
                    file_path = os.path.join(rid_folder_path, f'rid_{from_crs}_{to_crs}_{from_time}_{to_time}_{weekday}.json')
                    with open(file_path, 'w') as f1:
                        json.dump(rid_json, f1, indent=2)

                    combined = []

                    # get informations on all rids
                    for rid in rid_list:
                        details_json, failed_details = get_train_details(rid)
                        all_failed_details += failed_details
                        if details_json:
                            combined.append(details_json)
                    
                    # store all information inside one big file
                    file_path = os.path.join(details_folder_path, f'details_{from_crs}_{to_crs}_{from_time}_{to_time}_{weekday}.json')
                    with open(file_path, 'w') as f2:
                        json.dump(combined, f2, indent=2)
                
                #print('done with', from_crs, to_crs, from_time, to_time, weekday)
                break
           
            attempt += 1
        # if an error occurred
        except requests.exceptions.RequestException:
            # append start and end points to pull them later
            all_failed_rids.append([from_crs, to_crs, weekday])
            break
    
    # if request failed 5 times
    if attempt == 6:
        # append start and end points to pull them later
        all_failed_rids.append([from_crs, to_crs, weekday])

    # print(all_failed_rids, all_failed_details)

    # returns info of what start and end points failed and what rids failed
    return all_failed_rids, all_failed_details

# Worker function for fetching service details
def get_train_details(rid):
    details_json = None
    failed_local = []
    attempt = 1

    # try 5 times to get a response
    while attempt < 6:
        try:
            # get semaphore access
            with request_rights:
                # make the request
                response = requests.post(details_url, json={'rid': rid}, headers=headers)

            # if the request worked out
            if response.ok:
                details_json = response.json()
                break
            
            attempt += 1
        # if an error occurred
        except requests.exceptions.RequestException:
            # append rid to pull it later
            failed_local.append([rid])
            break
    
    # if request failed 5 times
    if attempt == 6:
        # append rid to pull it later
        failed_local.append([rid])

    # returns info on rid and whether it failed
    # failed_local should kinda be a value not a list but i think its fine
    return details_json, failed_local

# needed for sharing semaphore between processes
def init_worker(shared_semaphore):
    global request_rights
    request_rights = shared_semaphore

if __name__ == '__main__':
    # divide work
    times = [("0000", "0759"), ("0800", "1559"), ("1600", "2359")]
    weekdays = ['WEEKDAY', 'SATURDAY', 'SUNDAY']

    # create all the requests
    tasks = []
    for crs in crs_list:
        from_crs, to_crs = crs
        for from_time, to_time in times:
            for weekday in weekdays:
                tasks.append((from_crs, to_crs, from_time, to_time, weekday))
                tasks.append((to_crs, from_crs, from_time, to_time, weekday))

    # get all the shared datatypes ready
    manager = Manager()
    failed_rid = manager.list()
    failed_details = manager.list()
    request_rights = manager.Semaphore(4)

    failed_rid.append(['from', 'to', 'day'])
    failed_details.append(['rid'])

    # start = time.time()

    # start the processes
    with Pool(processes=6, initializer=init_worker, initargs=(request_rights,)) as pool:
        results = pool.map(get_hsp_data, tasks)

    # end = time.time()
    # print('elapsed:', end - start)

    # get info on waht failed
    rid_failed_local, details_failed_local = zip(*results)

    # join info into one big list
    for r in rid_failed_local:
        failed_rid.extend(r)

    # join info into one big list
    for r in details_failed_local:
        failed_details.extend(r)

    # store what failed
    with open("failed_rid.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(failed_rid)

    # store what failed
    with open("failed_details.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(failed_details)
