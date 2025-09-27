from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from chatbot.utils import process_query, generate_image  
from openai import OpenAI
from decouple import config  # <-- new

# Load API key from .env
OPENAI_API_KEY = config("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

@csrf_exempt
def get_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            language = data.get('language', 'en')  
            mode = data.get('mode', 'text')  # 'text' or 'image'

            # -----------------------
            # Image generation mode
            # -----------------------
            if mode == 'image':
                image_url = generate_image(user_message)
                if image_url:
                    return JsonResponse({'response': image_url})
                return JsonResponse({'response': "Sorry, I couldn't generate the image."})

            # -----------------------
            # Rule-based first
            # -----------------------
            response_text = process_query(user_message, language=language)

            # -----------------------
            # AI fallback if needed
            # -----------------------
            if response_text.strip() in ["", "One Moment Please!", "No data found"]:
                try:
                    ai_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful water resources assistant."},
                            {"role": "user", "content": user_message}
                        ]
                    )
                    response_text = ai_response.choices[0].message.content
                except Exception as e:
                    print("AI fallback error:", e)

            return JsonResponse({'response': response_text})

        except Exception as e:
            print("Error in chatbot:", e)
            return JsonResponse({'response': "Sorry, something went wrong."})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

def home(request):
    return render(request, 'home.html')