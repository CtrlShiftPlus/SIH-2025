# === IMPORTS ===
import json
import gradio as gr
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# === LOAD PHI-2 MODEL ===
model_id = "microsoft/phi-2"

print("⏳ Loading Phi-2 model (this may take a few seconds)...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
llm_pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

print("✅ Model loaded successfully.")

# === CONNECT TO MONGODB ===
client = MongoClient("mongodb://localhost:27017/")  # Change if needed
db = client["your_db_name"]                         # Replace with your DB name
collection = db["your_collection_name"]             # Replace with your collection name

# === GET GROUNDWATER DATA FROM MONGODB ===
def get_groundwater_data(location, year):
    try:
        doc = collection.find_one({f"{year}.locationName": location.upper()})
        if not doc:
            return None

        # Search the location in the list
        year_data = doc.get(year)
        for entry in year_data:
            if entry.get("locationName") == location.upper():
                return entry
        return None
    except Exception as e:
        print(f"MongoDB Error: {e}")
        return None

# === GENERATE CHATBOT RESPONSE WITH PHI-2 ===
def generate_phi2_response(context, question):
    prompt = f"""
You are a helpful assistant specialized in groundwater data.

Context:
{context}

Question: {question}
Answer:"""
    
    response = llm_pipe(prompt, max_new_tokens=200, do_sample=True, temperature=0.7)
    return response[0]['generated_text'].split("Answer:")[-1].strip()

# === MAIN CHAT FUNCTION ===
def groundwater_chatbot(location, year, question):
    data = get_groundwater_data(location, year)
    if not data:
        return f"⚠️ No data found for '{location}' in '{year}'."

    # Convert structured data to string
    context = json.dumps(data, indent=2)
    return generate_phi2_response(context, question)

# === GRADIO UI ===
def gradio_interface(location, year, question):
    return groundwater_chatbot(location, year, question)

interface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Textbox(label="📍 Location (e.g., NORTH 24 PARGANAS)"),
        gr.Textbox(label="📅 Year (e.g., 2012-2013)"),
        gr.Textbox(label="❓ Question (e.g., What is the total groundwater availability?)"),
    ],
    outputs="text",
    title="💧 Groundwater Chatbot (Free with Phi-2)",
    description="Ask questions about groundwater data using open-source AI and MongoDB."
)

# === LAUNCH APP ===
if __name__ == "__main__":
    interface.launch()
