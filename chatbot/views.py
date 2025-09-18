from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from chatbot.utils import process_query  

@csrf_exempt
def get_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            language = data.get('language', 'en')  


            response_text = process_query(user_message, language=language)

            return JsonResponse({'response': response_text})
        except Exception as e:
            print("Error in chatbot:", e)
            return JsonResponse({'response': "Sorry, something went wrong."})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

def home(request):
    return render(request, 'home.html')