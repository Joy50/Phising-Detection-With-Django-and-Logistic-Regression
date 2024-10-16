from django.shortcuts import render
from django.http import JsonResponse
import joblib
import pandas as pd
import requests
from ml.data_preprocessing import extract_url_features


# Your VirusTotal API key
API_KEY = "cfff5ff402ac88810a63b673ea1a81e6488a7a54dcbe4ba45b1240a15029900b"

# VirusTotal endpoints
BASE_URL = "https://www.virustotal.com/vtapi/v2/"
FILE_SCAN_URL = BASE_URL + "file/scan"
URL_SCAN_URL = BASE_URL + "url/scan"
FILE_REPORT_URL = BASE_URL + "file/report"
URL_REPORT_URL = BASE_URL + "url/report"

def get_url_report(resource):
    """Retrieve a report for a URL"""
    params = {'apikey': API_KEY, 'resource': resource}
    response = requests.get(URL_REPORT_URL, params=params)
    return response.json()


# Load the model once when the server starts
model = joblib.load('services/model.pkl')

# View to handle prediction
def predict_view(request):
    if request.method == 'POST':
        # Get the input data (URL) from the POST request
        input_data = request.POST.get('input_data')
        
        if not input_data:
            return JsonResponse({'error': 'No input data provided'}, status=400)
        
        try:
            # Extract features from the URL
            features = extract_url_features(input_data)
            
            # Convert the features dictionary into a DataFrame
            processed_data = pd.DataFrame([features])
            
            # Predict using the loaded model
            prediction = model.predict(processed_data)
            prediction_virus_total = get_url_report(input_data)
            
            # Return the prediction as a JSON response
            return JsonResponse({'prediction': int(prediction[0]),'virus_total':prediction_virus_total})
        
        except Exception as e:
            return JsonResponse({'error': f'Error processing input: {str(e)}'}, status=500)
    
    return render(request, 'index.html')
