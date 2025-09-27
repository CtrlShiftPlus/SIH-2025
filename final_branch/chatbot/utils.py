import os
import json
import re
from collections import defaultdict
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator
import spacy
from django.conf import settings
from openai import OpenAI
from decouple import config

# -------------------------------
# Translator
# -------------------------------
translator = GoogleTranslator(source="auto", target="en")

def translate_text(text, target_language='en'):
    if target_language == 'en':
        return text
    try:
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# -------------------------------
# Load Data
# -------------------------------
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

nlp = spacy.load("en_core_web_sm")

# -------------------------------
# OpenAI client
# -------------------------------
OPENAI_API_KEY = config("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------
# Helper functions
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
            "category": category,
            "rainfall": rec.get("rainfall", 0),
            "groundwater": rec.get("groundwater", 0)
        })
    return results

def generate_chart(records, filename="water_chart.png", metric="recharge", ylabel="Values", location="Unknown"):
    if not records:
        return None

    years = [rec.get("year") for rec in records]
    values = [rec.get(metric, 0) if not isinstance(rec.get(metric), dict) else
              rec[metric].get("total", rec[metric].get("level", 0)) for rec in records]

    plt.figure(figsize=(8, 5))
    plt.plot(years, values, marker="o", linestyle="-", color="blue", label=metric.capitalize())
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.title(f"{metric.capitalize()} Over Years in {location}")
    plt.legend()
    plt.grid(True)

    chart_dir = os.path.join(settings.BASE_DIR, "static", "chatbot", "images")
    os.makedirs(chart_dir, exist_ok=True)
    safe_loc = location.replace(" ", "_")
    filepath = os.path.join(chart_dir, f"{safe_loc}_{filename}")
    plt.savefig(filepath)
    plt.close()
    return f"/static/chatbot/images/{safe_loc}_{filename}"

# -------------------------------
# Parse query
# -------------------------------
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

# -------------------------------
# GPT fallback
# -------------------------------
def generate_ai_response(user_message):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful water resources assistant. Answer groundwater, recharge, rainfall and related queries. If possible, use the latest data from public sources."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API error:", e)
        return "Sorry, I'm having trouble connecting to the AI service."

# -------------------------------
# Image generation
# -------------------------------
def generate_image(prompt, size="512x512"):
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size
        )
        return response.data[0].url
    except Exception as e:
        print("Image generation error:", e)
        return None

# -------------------------------
# Main query processor
# -------------------------------
def process_query(query, language="en"):
    q = query.lower()
    # Greeting
    if q in ["hi", "hello", "hey"]:
        return "Hi! How may I help you today?"

    state, district, year, create_chart = parse_query(query)
    location_type, location_name = extract_location(query)
    records = get_water_data(state_name=state, district_name=district, year=year)

    response = ""

    if "how much water" in q or "recharge" in q:
        total = sum(r.get("recharge", 0) for r in records)
        if total == 0:
            records = []  # fallback to GPT
        else:
            avg = total / len(records)
            response = f"Total recharge: {total}, Average recharge: {avg:.2f}"

    elif "rainfall" in q or "rain water" in q:
        rainfall_vals = []
        for r in records:
            rf = r.get("rainfall", 0)
            if isinstance(rf, dict):
                rf = rf.get("total") or 0
            rainfall_vals.append(rf)
        total_rainfall = sum(rainfall_vals)
        if total_rainfall == 0:
            records = []
        else:
            avg_rainfall = total_rainfall / len(rainfall_vals)
            response = f"Total rainfall: {total_rainfall}, Average rainfall: {avg_rainfall:.2f}"

    elif "groundwater" in q or "water level" in q:
        gw_vals = []
        for r in records:
            gw = r.get("groundwater", 0)
            if isinstance(gw, dict):
                gw = gw.get("level") or gw.get("total") or 0
            gw_vals.append(gw)
        total_gw = sum(gw_vals)
        if total_gw == 0:
            records = []
        else:
            avg_gw = total_gw / len(gw_vals)
            response = f"Total groundwater level: {total_gw}, Average groundwater level: {avg_gw:.2f}"

    elif "loss" in q:
        total_loss = sum(r.get("loss_total", 0) for r in records)
        if total_loss == 0:
            records = []
        else:
            response = f"Total water loss: {total_loss}"

    elif "status" in q or "category" in q:
        categories = list({r.get("category", "unknown") for r in records})
        if not categories or categories == ["unknown"]:
            records = []
        else:
            response = f"Water status/category: {', '.join(categories)}"

    elif "safe to extract" in q:
        avg_recharge = sum(r.get("recharge", 0) for r in records) / len(records) if records else 0
        response = "Yes, it is safe to extract water." if avg_recharge > 100 else "No, water extraction is risky."

    # Chart generation
    if create_chart and records:
        metric = "recharge"
        if "rainfall" in q:
            metric = "rainfall"
        elif "groundwater" in q:
            metric = "groundwater"
        chart_path = generate_chart(records, filename=f"{metric}_chart.png", metric=metric, location=location_name)
        if chart_path:
            response += f"\nVisualization: <a href='{chart_path}' target='_blank'>Click here to view the chart</a>"

    # Translate if needed
    if language != "en" and response:
        try:
            response = GoogleTranslator(source='en', target=language).translate(response)
        except Exception as e:
            print(f"Translation error: {e}")

    # If no local data, use GPT
    if not response:
        response = generate_ai_response(query)

    return response or "Sorry, no data found."