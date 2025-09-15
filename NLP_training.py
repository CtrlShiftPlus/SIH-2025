#code works intermediately on google collab could give better answers

import json
import spacy
from collections import defaultdict

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load your .json data
with open("allyears_data.json", "r") as f:
    data = json.load(f)

# Create a mapping for state-wise data (for quick lookup)
state_data = defaultdict(list)

for year, districts in data.items():
    for district in districts:
        state_data[district["stateName"]].append(district)

# Example: Let's see what the structure looks like
print(state_data.keys())  # List of states in your data

# Function to process and clean the query
def process_query(query):
    query = query.lower().strip()
    return query

# Function to match query and return answers
def get_answer(query):
    query = process_query(query)
    
    # Look for specific keywords in the query (e.g., "groundwater", "rainfall", etc.)
    if "groundwater" in query:
        return get_groundwater_data(query)
    elif "rainfall" in query:
        return get_rainfall_data(query)
    elif "recharge-worthy" in query:
        return get_recharge_worthy_area(query)
    elif "safe blocks" in query:
        return get_safe_blocks(query)
    elif "criticality" in query or "category" in query:
        return get_criticality(query)
    else:
        return "Sorry, I could not understand your question. Please ask something else."

# Get groundwater data based on state and year
def get_groundwater_data(query):
    # Example: extract state from query (this part can be expanded further)
    location_type, location_name = extract_location(query)
    
    if location_type == "Unknown":
        return f"Sorry, I could not identify the state or district in your question."
    
    if location_type == "state":
        if location_name in state_data:
            total_gw = sum(d.get("totalGWAvailability", {}).get("total", 0) for d in state_data[location_name])
            return f"Total groundwater available in {location_name}: {total_gw} cubic meters."
        else:
            return f"Sorry, I could not find groundwater data for {location_name}."
    
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    total_gw = district.get("totalGWAvailability", {}).get("total", "N/A")
                    return f"Total groundwater available in {location_name}: {total_gw} cubic meters."
    
    return f"Sorry, I could not find groundwater data for {location_name}."

# Function to extract state or district from query using spaCy
def extract_location(query):
    for state in state_data.keys():
        if state.lower() in query:
            return "state", state
    
    # If it's a district query, look for it in the districts
    for state, districts in state_data.items():
        for district in districts:
            if district.get("locationName", "").lower() in query:
                return "district", district["locationName"]
    
    return "Unknown", ""

# Function to get criticality (stage of extraction) data
def get_criticality(query):
    location_type, location_name = extract_location(query)
    
    if location_type == "Unknown":
        return "Sorry, I couldn't identify the state or district in your question."
    
    if location_type == "state":
        if location_name in state_data:
            criticality = []
            for district in state_data[location_name]:
                # Check if the 'category' or 'total' is available and valid
                category = district.get("category", {})
                stage_of_extraction = category.get("total", "N/A") if category else "N/A"
                
                # Only append valid data
                if stage_of_extraction != "N/A":
                    criticality.append(stage_of_extraction)
            
            if criticality:
                return f"The groundwater criticality (stage of extraction) in {location_name} is: {', '.join(set(criticality))}."
            else:
                return f"Sorry, no groundwater criticality data is available for {location_name}."
        
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    # Same safe check for district level
                    category = district.get("category", {})
                    stage_of_extraction = category.get("total", "N/A") if category else "N/A"
                    
                    if stage_of_extraction != "N/A":
                        return f"The groundwater criticality (stage of extraction) in {location_name} is: {stage_of_extraction}."
                    else:
                        return f"Sorry, no groundwater criticality data is available for {location_name}."
    
    return f"Sorry, I could not find criticality data for {location_name}."

# Additional functions for other queries (e.g., rainfall, recharge-worthy area, etc.)
def get_rainfall_data(query):
    location_type, location_name = extract_location(query)
    
    if location_type == "Unknown":
        return f"Sorry, I could not identify the state or district in your question."
    
    if location_type == "state":
        if location_name in state_data:
            total_rainfall = sum(d.get("rainfall", {}).get("total", 0) for d in state_data[location_name])
            return f"Total rainfall in {location_name}: {total_rainfall} mm."
        else:
            return f"Sorry, I could not find rainfall data for {location_name}."
    
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    total_rainfall = district.get("rainfall", {}).get("total", "N/A")
                    return f"Total rainfall in {location_name}: {total_rainfall} mm."
    
    return f"Sorry, I could not find rainfall data for {location_name}."

def get_recharge_worthy_area(query):
    location_type, location_name = extract_location(query)
    
    if location_type == "Unknown":
        return f"Sorry, I could not identify the state or district in your question."
    
    if location_type == "state":
        if location_name in state_data:
            total_area = sum(d.get("area", {}).get("recharge_worthy", {}).get("totalArea", 0) for d in state_data[location_name])
            return f"Total recharge-worthy area in {location_name}: {total_area} hectares."
        else:
            return f"Sorry, I could not find recharge-worthy area data for {location_name}."
    
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    total_area = district.get("area", {}).get("recharge_worthy", {}).get("totalArea", "N/A")
                    return f"Total recharge-worthy area in {location_name}: {total_area} hectares."
    
    return f"Sorry, I could not find recharge-worthy area data for {location_name}."

def get_safe_blocks(query):
    location_type, location_name = extract_location(query)
    
    if location_type == "Unknown":
        return f"Sorry, I could not identify the state or district in your question."
    
    if location_type == "state":
        if location_name in state_data:
            safe_blocks = sum(1 for d in state_data[location_name] if d.get("reportSummary", {}).get("total", {}).get("BLOCK", {}).get("safe", 0) > 0)
            return f"Total safe blocks in {location_name}: {safe_blocks}."
        else:
            return f"Sorry, I could not find safe block data for {location_name}."
    
    elif location_type == "district":
        for state, districts in state_data.items():
            for district in districts:
                if district.get("locationName") == location_name:
                    safe_blocks = district.get("reportSummary", {}).get("total", {}).get("BLOCK", {}).get("safe", 0)
                    return f"Total safe blocks in {location_name}: {safe_blocks}."
    
    return f"Sorry, I could not find safe block data for {location_name}."

# Start the chatbot
def chatbot():
    print("Welcome to the Groundwater Query Chatbot!")
    print("You can ask about groundwater, rainfall, recharge-worthy area, safe blocks, criticality, and more.")
    print("Type 'exit' to end the chat.")
    
    while True:
        query = input("You: ").lower()
        if query == 'exit':
            print("Goodbye!")
            break
        else:
            response = get_answer(query)
            print(f"Bot: {response}")

# Start the interactive chatbot
chatbot()
