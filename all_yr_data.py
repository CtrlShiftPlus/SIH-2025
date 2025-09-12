import requests
import time
import json
import csv

# API endpoint
url = "https://ingres.iith.ac.in/api/gec/getBusinessDataForUserOpen"

# Headers to mimic browser request
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://ingres.iith.ac.in",
    "Referer": "https://ingres.iith.ac.in/gecdataonline/misview",
}

# Common payload parameters
common_payload = {
    "approvalLevel": 1,
    "category": "all",
    "component": "recharge",
    "computationType": "normal",
    "period": "annual",
    "stateuuid": None,
    "verificationStatus": 1,
    "view": "admin",
}

# All years (manually listed for now)
years = [
    "2012-2013", "2013-2014", "2014-2015", "2015-2016",
    "2016-2017", "2017-2018", "2018-2019", "2019-2020",
    "2020-2021", "2021-2022", "2022-2023", "2023-2024",
    "2024-2025"
]

# Dictionary to hold year-indexed data
all_data = {}

for year in years:
    print(f"\n📡 Fetching data for year: {year}")

    # Step 1: Fetch states
    state_payload = {
        **common_payload,
        "year": year,
        "locname": "INDIA",
        "loctype": "COUNTRY",
        "locuuid": "ffce954d-24e1-494b-ba7e-0931d8ad6085",
        "parentuuid": "ffce954d-24e1-494b-ba7e-0931d8ad6085",
    }

    state_response = requests.post(url, headers=headers, json=state_payload)
    if state_response.status_code != 200:
        print(f"❌ Failed to get states for {year}")
        continue

    states = state_response.json()
    year_data = []

    # Step 2: Loop through states → fetch districts
    for state in states:
        state_name = state.get("locationName", "Unknown")
        state_uuid = state.get("locationUUID", None)
        if not state_uuid:
            continue

        district_payload = {
            **common_payload,
            "year": year,
            "locname": state_name,
            "loctype": "STATE",
            "locuuid": state_uuid,
            "parentuuid": state_uuid,
        }

        district_response = requests.post(url, headers=headers, json=district_payload)
        if district_response.status_code == 200:
            districts = district_response.json()
            print(f"   ✅ {len(districts)} districts in {state_name} ({year})")

            for d in districts:
                d["year"] = year
                d["stateName"] = state_name
                year_data.append(d)
        else:
            print(f"   ❌ Failed to get districts for {state_name} in {year}")

        time.sleep(1)  # polite delay

    all_data[year] = year_data
    print(f"📁 Collected {len(year_data)} district records for {year}")

# Step 3: Save year-indexed JSON
output_json = "all_district_data.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2)

print(f"\n📁 Saved all data (year-indexed) to {output_json}")

# Step 4: Save as single CSV
output_csv = "all_district_data.csv"
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    header = ["year", "stateName", "locationName", "locationType",
              "stageOfExtraction", "totalRecharge", "category"]
    writer.writerow(header)

    for year, records in all_data.items():
        for record in records:
            row = [
                record.get("year", ""),
                record.get("stateName", ""),
                record.get("locationName", ""),
                record.get("locationType", ""),
                record.get("stageOfExtraction", ""),
                record.get("totalRecharge", record.get("groundWaterRecharge", "")),
                record.get("category", ""),
            ]
            writer.writerow(row)

print(f"📁 Saved all data (flat table) to {output_csv}")
print("\n🎉 Done! All years collected and indexed successfully.")