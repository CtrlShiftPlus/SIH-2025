import os
import json
import re
from difflib import get_close_matches
import matplotlib.pyplot as plt
from googletrans import Translator
import spacy
from collections import defaultdict

# -------------------------------
# Load JSON Data
# -------------------------------
with open("allyears_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Flatten JSON
all_records = []
for year_key, year_records in data.items():
    for rec in year_records:
        rec["year"] = year_key
        all_records.append(rec)

# Create state-wise mapping
state_data = defaultdict(list)
for year, districts in data.items():
    for district in districts:
        state_data[district["stateName"]].append(district)

# -------------------------------
# Setup Translator & NLP
# -------------------------------
translator = Translator()
nlp = spacy.load("en_core_web_sm")

# -------------------------------
# Helper: Extract location
# -------------------------------
def extract_location(query):
    query = query.lower()
    for state in state_data.keys():
        if state.lower() in query:
            return "state", state
    for state, districts in state_data.items():
        for district in districts:
            if district.get("locationName", "").lower() in query:
                return "district", district["locationName"]
    return "Unknown", ""

# -------------------------------
# Old helpers (chart, data)
# -------------------------------
def get_water_data(state_name=None, district_name=None, year=None):
    results = []
    for rec in all_records:
        if not isinstance(rec, dict):
            continue

        state = rec.get("stateName", "").lower()
        district = rec.get("locationName", "").lower()
        yr = rec.get("year", "")

        if state_name and state != state_name.lower():
            continue
        if district_name and district != district_name.lower():
            continue
        if year and year != yr:
            continue

        category = "unknown"
        if rec.get("category") and isinstance(rec.get("category"), dict):
            category = rec["category"].get("total", "unknown")

        results.append({
            "state": rec.get("stateName"),
            "district": rec.get("locationName"),
            "year": yr,
            "recharge": rec.get("area", {}).get("recharge_worthy", {}).get("totalArea", 0),
            "loss_total": rec.get("loss", {}).get("total", 0),
            "category": category
        })
    return results


def generate_chart(records, filename="water_chart.png"):
    if not records:
        return None

    years = [rec.get("year") for rec in records]
    values = [rec.get("recharge", 0) for rec in records]

    plt.figure(figsize=(8, 5))
    plt.plot(years, values, marker="o", linestyle="-", color="blue", label="Recharge")
    plt.xlabel("Year")
    plt.ylabel("Recharge (Total Area)")
    plt.title("Water Recharge Over Years")
    plt.legend()
    plt.grid(True)

    os.makedirs("images", exist_ok=True)
    filepath = os.path.join("images", filename)
    plt.savefig(filepath)
    plt.close()
    return filepath

# -------------------------------
# New helpers (second chatbot)
# -------------------------------
def get_groundwater_data(location_type, location_name):
    if location_type == "state":
        if location_name in state_data:
            total_gw = sum(d.get("totalGWAvailability", {}).get("total", 0) for d in state_data[location_name])
            return f"Total groundwater available in {location_name}: {total_gw} cubic meters."
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    total_gw = district.get("totalGWAvailability", {}).get("total", "N/A")
                    return f"Total groundwater available in {location_name}: {total_gw} cubic meters."
    return f"Sorry, I could not find groundwater data for {location_name}."


def get_rainfall_data(location_type, location_name):
    if location_type == "state":
        if location_name in state_data:
            total_rainfall = sum(d.get("rainfall", {}).get("total", 0) for d in state_data[location_name])
            return f"Total rainfall in {location_name}: {total_rainfall} mm."
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    total_rainfall = district.get("rainfall", {}).get("total", "N/A")
                    return f"Total rainfall in {location_name}: {total_rainfall} mm."
    return f"Sorry, I could not find rainfall data for {location_name}."


def get_recharge_worthy_area(location_type, location_name):
    if location_type == "state":
        if location_name in state_data:
            total_area = sum(d.get("area", {}).get("recharge_worthy", {}).get("totalArea", 0) for d in state_data[location_name])
            return f"Total recharge-worthy area in {location_name}: {total_area} hectares."
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    total_area = district.get("area", {}).get("recharge_worthy", {}).get("totalArea", "N/A")
                    return f"Total recharge-worthy area in {location_name}: {total_area} hectares."
    return f"Sorry, I could not find recharge-worthy area data for {location_name}."


def get_safe_blocks(location_type, location_name):
    if location_type == "state":
        if location_name in state_data:
            safe_blocks = sum(1 for d in state_data[location_name] if d.get("reportSummary", {}).get("total", {}).get("BLOCK", {}).get("safe", 0) > 0)
            return f"Total safe blocks in {location_name}: {safe_blocks}."
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    safe_blocks = district.get("reportSummary", {}).get("total", {}).get("BLOCK", {}).get("safe", 0)
                    return f"Total safe blocks in {location_name}: {safe_blocks}."
    return f"Sorry, I could not find safe block data for {location_name}."


def get_criticality(location_type, location_name):
    if location_type == "state":
        if location_name in state_data:
            crit = [d.get("category", {}).get("total", "N/A") for d in state_data[location_name] if d.get("category")]
            crit = [c for c in crit if c != "N/A"]
            if crit:
                return f"Groundwater criticality in {location_name}: {', '.join(set(crit))}."
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    stage = district.get("category", {}).get("total", "N/A")
                    if stage != "N/A":
                        return f"Groundwater criticality in {location_name}: {stage}."
    return f"Sorry, I could not find criticality data for {location_name}."

# -------------------------------
# Unified process_query
# -------------------------------

# -------------------------------
# Query Parser
# -------------------------------
def parse_query(query):
    query_lower = query.lower()
    state = None
    district = None
    year = None
    create_chart = False

    # Find state
    for s in state_data.keys():
        if s.lower() in query_lower:
            state = s
            break

    # Find district
    for s, districts in state_data.items():
        for d in districts:
            loc = d.get("locationName", "").lower()
            if loc and loc in query_lower:
                district = d.get("locationName")
                break

    # Find year (4-digit)
    match = re.search(r"\b(19|20)\d{2}\b", query_lower)
    if match:
        year = match.group(0)

    # If user asked for chart/graph
    if "chart" in query_lower or "graph" in query_lower or "plot" in query_lower:
        create_chart = True

    return state, district, year, create_chart

def process_query(query, language="en"):
    query_lower = query.lower()
    response = ""

    # Detect location
    location_type, location_name = extract_location(query)

    # ------------------------
    # Handle second chatbot queries
    # ------------------------
    if "groundwater" in query_lower:
        response = get_groundwater_data(location_type, location_name)
    elif "rainfall" in query_lower:
        response = get_rainfall_data(location_type, location_name)
    elif "recharge-worthy" in query_lower or "recharge worthy" in query_lower:
        response = get_recharge_worthy_area(location_type, location_name)
    elif "safe blocks" in query_lower:
        response = get_safe_blocks(location_type, location_name)
    elif "criticality" in query_lower or "stage" in query_lower or "category" in query_lower:
        response = get_criticality(location_type, location_name)

    # ------------------------
    # Handle first chatbot queries
    # ------------------------
    else:
        state, district, year, create_chart = parse_query(query)
        records = get_water_data(state_name=state, district_name=district, year=year)

        if not records:
            response = f"No data found for the query: {query}"
        else:
            if "how much water" in query_lower:
                total = sum(r.get("recharge", 0) for r in records)
                response = f"Total water available is {total}."
            elif "safe to extract" in query_lower:
                avg_recharge = sum(r.get("recharge", 0) for r in records) / len(records)
                response = "Yes, it is safe to extract water." if avg_recharge > 100 else "No, water extraction is risky."
            elif "status" in query_lower:
                categories = list({r.get("category", "unknown") for r in records})
                response = f"Water status/category: {', '.join(categories)}"
            elif "loss" in query_lower:
                total_loss = sum(r.get("loss_total", 0) for r in records)
                response = f"Total water loss: {total_loss}"
            else:
                response = "Sorry, I don't understand that query."

            if create_chart:
                chart_name = f"{state or district}_water_chart.png"
                chart_path = generate_chart(records, chart_name)
                if chart_path:
                    response += f"\nVisualization saved at: {chart_path}"

    # ------------------------
    # Translate if needed
    # ------------------------
    if language != "en":
        translated = translator.translate(response, dest=language)
        response = translated.text

    return response

# -------------------------------
# Main Loop
# -------------------------------
if __name__ == "__main__":
    print("💧 Unified Water Data Chatbot")
    print("Ask about: groundwater, rainfall, recharge-worthy area, safe blocks, criticality, water loss, safe extraction, etc.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Exiting chatbot. Bye 👋")
            break

        lang = input("Language (en/hi/kn/te/mr/ta/gu): ").lower()
        if lang not in ["en", "hi", "kn", "te", "mr", "ta", "gu"]:
            lang = "en"

        print("Bot:", process_query(query, language=lang))
