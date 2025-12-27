import requests
import csv
import time
from datetime import datetime


base_url = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
company_name = "JPMORGAN CHASE & CO."
output_file = "chase_complaints_2025_full.csv"

# We would like to have complaints from 2025 only
months = [f"2025-{m:02d}-01" for m in range(1, 13)]

all_complaints = []
headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) python-requests/2.31'
}

for start_date in months:
    print(f"--- Processing {start_date} ---")
    dt_start = datetime.strptime(start_date, "%Y-%m-%d")
    if dt_start.month == 12:
        dt_end = dt_start.replace(year=dt_start.year + 1, month=1)
    else:
        dt_end = dt_start.replace(month=dt_start.month + 1)
    end_date = dt_end.strftime("%Y-%m-%d")

    offset = 0
    size = 500  # Smaller chunks to be safer with rate limits
    
    while True:
        params = {
            'company': company_name,
            'has_narrative': 'true',
            'date_received_min': start_date,
            'date_received_max': end_date,
            'size': size,
            'frm': offset
        }

        try:
            response = requests.get(base_url, params=params, headers=headers)
            
            # Handle Rate Limiting (429)
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 30))
                print(f"Rate limited! Sleeping for {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            hits_data = data.get('hits', {})
            hits_list = hits_data.get('hits', [])
            
            # Handle the "total" object structure in ES 7+
            total_info = hits_data.get('total', 0)
            total_for_period = total_info.get('value', 0) if isinstance(total_info, dict) else total_info

            if not hits_list:
                break

            for hit in hits_list:
                # _source contains all raw columns from the CFPB
                all_complaints.append(hit['_source'])

            print(f"  Retrieved {len(all_complaints)} total records (Offset: {offset})")
            
            offset += size
            if offset >= total_for_period:
                break
            
            time.sleep(1.0) # Delay between requests

        except Exception as e:
            print(f"Error at {start_date} offset {offset}: {e}")
            break

if all_complaints:
    # Get all possible column headers from the keys of the complaints
    keys = all_complaints[0].keys()
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_complaints)
    print(f"\nSuccess! Saved {len(all_complaints)} records to {output_file}")
else:
    print("\nNo records were retrieved.")