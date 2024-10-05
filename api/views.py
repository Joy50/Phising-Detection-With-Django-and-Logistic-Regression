from django.shortcuts import render
from django.http import JsonResponse
import joblib
import numpy as np
import pandas as pd
from urllib.parse import urlparse
import math
import re


# Load the model once when the server starts
model = joblib.load('services/model.pkl')

# Feature extraction function
def extract_url_features(url: str):
    # Parse the URL using urllib
    parsed_url = urlparse(url)
    
    # Extracting the domain, path, and other components
    hostname = parsed_url.hostname or ""
    path = parsed_url.path or ""
    query = parsed_url.query or ""

    # Defining feature extraction for each parameter
    features = {
        'NumDots': url.count('.'),
        'SubdomainLevel': hostname.count('.'),
        'PathLevel': path.count('/'),
        'UrlLength': len(url),
        'NumDash': url.count('-'),
        'NumDashInHostname': hostname.count('-'),
        'AtSymbol': url.count('@'),
        'TildeSymbol': url.count('~'),
        'NumUnderscore': url.count('_'),
        'NumPercent': url.count('%'),
        'NumQueryComponents': len(query.split('&')) if query else 0,
        'NumAmpersand': query.count('&'),
        'NumHash': url.count('#'),
        'NumNumericChars': sum(c.isdigit() for c in url),
        'NoHttps': int(not url.startswith('https')),
        'RandomString': int(is_random_string(url)),  # Custom function to determine randomness
        'IpAddress': int(is_ip_address(hostname)),  # Check if the hostname is an IP address
        'DomainInSubdomains': int(domain_in_subdomains(hostname)),  # Custom logic to check domain
        'DomainInPaths': int(domain_in_paths(path)),  # Custom logic to check domain in path
        'HttpsInHostname': int('https' in hostname),
        'HostnameLength': len(hostname),
        'PathLength': len(path),
        'QueryLength': len(query),
        'DoubleSlashInPath': int('//' in path),
        'NumSensitiveWords': count_sensitive_words(url),  # Custom function for sensitive words
        'EmbeddedBrandName': int(is_brand_embedded(url)),  # Custom function for brand embedding
        'PctExtHyperlinks': 0,  # Placeholder
        'PctExtResourceUrls': 0,  # Placeholder
        'ExtFavicon': 0,  # Placeholder
        'InsecureForms': 0,  # Placeholder
        'RelativeFormAction': 0,  # Placeholder
        'ExtFormAction': 0,  # Placeholder
        'AbnormalFormAction': 0,  # Placeholder
        'PctNullSelfRedirectHyperlinks': 0,  # Placeholder
        'FrequentDomainNameMismatch': 0,  # Placeholder
        'FakeLinkInStatusBar': 0,  # Placeholder
        'RightClickDisabled': 0,  # Placeholder
        'PopUpWindow': 0,  # Placeholder
        'SubmitInfoToEmail': 0,  # Placeholder
        'IframeOrFrame': 0,  # Placeholder
        'MissingTitle': 0,  # Placeholder
        'ImagesOnlyInForm': 0,  # Placeholder
        'SubdomainLevelRT': 0,  # Placeholder
        'UrlLengthRT': 0,  # Placeholder
        'PctExtResourceUrlsRT': 0,  # Placeholder
        'AbnormalExtFormActionR': 0,  # Placeholder
        'ExtMetaScriptLinkRT': 0,  # Placeholder
        'PctExtNullSelfRedirectHyperlinksRT': 0,  # Placeholder
    }
    
    return features

# Helper functions to check for specific conditions:
def is_ip_address(hostname):
    try:
        ip = hostname.split('.')
        return len(ip) == 4 and all(0 <= int(part) < 256 for part in ip)
    except ValueError:
        return False

def is_random_string(url):
    """
    Detects whether a given string (URL) is random based on entropy and character patterns.
    """
    # Calculate Shannon entropy for the string
    def shannon_entropy(s):
        # Create a frequency dictionary of characters
        freq = {}
        for c in s:
            if c in freq:
                freq[c] += 1
            else:
                freq[c] = 1
        
        # Total length of the string
        length = len(s)
        
        # Shannon entropy calculation
        entropy = 0.0
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy
    
    # Entropy threshold (you can tweak this based on testing)
    entropy_threshold = 4.0  # A high entropy indicates randomness
    
    # Check if the URL contains long sequences of letters or digits
    # This will capture patterns like: "asdf1234" or "abcxyz"
    long_random_pattern = re.compile(r"[a-zA-Z0-9]{10,}")  # Sequences of 10+ characters
    
    # Calculate the entropy of the URL
    entropy_score = shannon_entropy(url)
    
    # Check for long sequences of characters/digits that seem random
    if entropy_score > entropy_threshold or long_random_pattern.search(url):
        return True  # Flag as random if entropy is high or random patterns are found
    
    return False  # Otherwise, it doesn't seem random



from urllib.parse import urlparse

def domain_in_subdomains(hostname):
    """
    Checks if the domain is embedded within the subdomains of the hostname.
    For example, in "google.fake-domain.com", 'google' is embedded in the subdomain.
    """
    # Extract the main domain by splitting the hostname
    parts = hostname.split('.')
    
    # Return False if the hostname is too short to have subdomains
    if len(parts) < 3:
        return False
    
    # Extract the last two parts as the actual domain and TLD (e.g., 'domain.com')
    main_domain = ".".join(parts[-2:])
    
    # Extract subdomains (everything except the main domain and TLD)
    subdomains = parts[:-2]
    
    # Check if any part of the main domain appears in the subdomains
    for subdomain in subdomains:
        if main_domain.split('.')[0] in subdomain:
            return True
    
    return False


def domain_in_paths(path):
    return False

def count_sensitive_words(url):
    sensitive_words = ['login', 'secure', 'account', 'update', 'confirm']
    return sum(url.lower().count(word) for word in sensitive_words)

def is_brand_embedded(url):
    return False

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
            
            # Return the prediction as a JSON response
            return JsonResponse({'prediction': int(prediction[0])})
        
        except Exception as e:
            return JsonResponse({'error': f'Error processing input: {str(e)}'}, status=500)
    
    return render(request, 'index.html')
