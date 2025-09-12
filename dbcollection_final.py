import requests
import time
import json

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

# Common payload parameters for all requests
common_payload = {
    "approvalLevel": 1,
    "category": "all",
    "component": "recharge",
    "computationType": "normal",
    "period": "annual",
    "stateuuid": None,
    "verificationStatus": 1,
    "view": "admin",
    "year": "2024-2025"
}

# Step 1: Fetch all states
state_payload = {
    **common_payload,
    "locname": "INDIA",
    "loctype": "COUNTRY",
    "locuuid": "ffce954d-24e1-494b-ba7e-0931d8ad6085",
    "parentuuid": "ffce954d-24e1-494b-ba7e-0931d8ad6085",
}

print("📡 Fetching all states data...")
state_response = requests.post(url, headers=headers, json=state_payload)

if state_response.status_code != 200:
    print(f"❌ Failed to get states data. HTTP Status: {state_response.status_code}")
    exit()

states = state_response.json()
print(f"✅ Retrieved {len(states)} states.")

# Step 2: For each state, fetch district data
all_districts = []

for state in states:
    state_name = state["locationName"]
    state_uuid = state["locationUUID"]

    district_payload = {
        **common_payload,
        "locname": state_name,
        "loctype": "STATE",
        "locuuid": state_uuid,
        "parentuuid": state_uuid,
    }

    print(f"📡 Fetching districts for state: {state_name}")
    district_response = requests.post(url, headers=headers, json=district_payload)

    if district_response.status_code == 200:
        districts = district_response.json()
        print(f"✅ Found {len(districts)} districts in {state_name}")
        all_districts.extend(districts)
    else:
        print(f"❌ Failed to get districts for {state_name}. HTTP Status: {district_response.status_code}")

    time.sleep(1)  # polite delay to avoid hammering the server

# Step 3: Save all districts data to a JSON file
output_file = "all_district_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_districts, f, indent=2)

print(f"\n🎉 Done! Total districts collected: {len(all_districts)}")
print(f"📁 Saved all district data to {output_file}")
