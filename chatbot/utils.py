import os
import json
import re
from difflib import get_close_matches
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator
import spacy
from collections import defaultdict
import os
from django.conf import settings



translator = GoogleTranslator(source="auto", target="en")

def translate_text(text, target_language='en'):
    if target_language == 'en':
        return text
    try:
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def handle_message_in_english(message):
    return f"Echo: {message}"

def process_query(user_message, language="en"):
    if language != "en":
        user_message = translate_text(user_message, target_language='en')

    response = handle_message_in_english(user_message)


    if language != "en":
        response = translate_text(response, target_language=language)

    return response

DATA_FILE = os.path.join(settings.BASE_DIR, "chatbot", "allyears_data.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)



all_records = []
for year_key, year_records in data.items():
    for rec in year_records:
        rec["year"] = year_key
        all_records.append(rec)


state_data = defaultdict(list)
for year, districts in data.items():
    for district in districts:
        state_data[district["stateName"]].append(district)


translator = GoogleTranslator(source="auto", target="en")
nlp = spacy.load("en_core_web_sm")


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


def generate_chart(records, filename="water_chart.png", metric="recharge", ylabel="Recharge (Total Area)"):
    if not records:
        return None

    years = [rec.get("year") for rec in records]
    values = [rec.get(metric, 0) for rec in records]

    plt.figure(figsize=(8, 5))
    plt.plot(years, values, marker="o", linestyle="-", color="blue", label=metric.capitalize())
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.title(f"{metric.capitalize()} Over Years")
    plt.legend()
    plt.grid(True)

    # Save inside static folder
    chart_dir = os.path.join(settings.BASE_DIR, "static", "chatbot", "images")
    os.makedirs(chart_dir, exist_ok=True)
    filepath = os.path.join(chart_dir, filename)
    plt.savefig(filepath)
    plt.close()
    return f"/static/chatbot/images/{filename}"



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


def parse_query(query):
    query_lower = query.lower()
    state = None
    district = None
    year = None
    create_chart = False


    for s in state_data.keys():
        if s.lower() in query_lower:
            state = s
            break


    for s, districts in state_data.items():
        for d in districts:
            loc = d.get("locationName", "").lower()
            if loc and loc in query_lower:
                district = d.get("locationName")
                break


    match = re.search(r"\b(19|20)\d{2}\b", query_lower)
    if match:
        year = match.group(0)


    if "chart" in query_lower or "graph" in query_lower or "plot" in query_lower:
        create_chart = True

    return state, district, year, create_chart

def process_query(query, language="en"):
    query_lower = query.lower()
    response = ""
    response_parts = []  


    location_type, location_name = extract_location(query)


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
                response = "One Moment Please!"

            if create_chart:
                chart_name = f"{state or district}_water_chart.png"
                chart_path = generate_chart(records, chart_name)
                if chart_path:
                    response += f"\nVisualization: <a href='{chart_path}' target='_blank'>Click here to view the chart</a>"


    if language != "en":
        try:
            response = GoogleTranslator(source='en', target=language).translate(response)
        except Exception as e:
            print(f"Translation error: {e}")

    return response

