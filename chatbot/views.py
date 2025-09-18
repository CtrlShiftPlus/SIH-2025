from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from chatbot.utils import process_query
  # your existing chatbot processing function
from deep_translator import GoogleTranslator  # ensure you have googletrans installed

# Initialize the translator outside the view for efficiency
translator = GoogleTranslator(source="auto", target="en")

@csrf_exempt
def get_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            language = data.get('language', 'en')  # default to English if not provided

            # --- Translate user's message to English if needed ---
            if language != 'en':
                translated = translator.translate(user_message, dest='en')
                user_message_en = translated.text
            else:
                user_message_en = user_message

            # --- Process the message in English ---
            bot_response_en = process_query(user_message_en)

            # --- Translate bot response back to user's language if needed ---
            if language != 'en':
                translated_response = translator.translate(bot_response_en, dest=language)
                bot_response = translated_response.text
            else:
                bot_response = bot_response_en

            return JsonResponse({'response': bot_response})
        except Exception as e:
            print("Error in chatbot:", e)  # Log the error
            return JsonResponse({'response': "Sorry, something went wrong."})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def home(request):
    return render(request, 'home.html')