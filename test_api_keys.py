import os
import sys
from dotenv import load_dotenv
load_dotenv()

print('=== Testing API Keys ===\n')

# Test OpenAI API Key
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f'1. OPENAI_API_KEY: Found ({openai_key[:20]}...)')
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        models = client.models.list()
        print('   Status: VALID')
    except Exception as e:
        print(f'   Status: ERROR - {str(e)[:80]}')
else:
    print('1. OPENAI_API_KEY: NOT FOUND')

# Test NewsAPI Key  
newsapi_key = os.getenv('NEWSAPI_KEY')
if newsapi_key:
    print(f'2. NEWSAPI_KEY: Found ({newsapi_key[:10]}...)')
    try:
        import requests
        response = requests.get('https://newsapi.org/v2/everything', params={'q':'test','apiKey':newsapi_key,'pageSize':1}, timeout=5)
        if response.status_code == 200:
            print('   Status: VALID')
        else:
            print(f'   Status: ERROR - HTTP {response.status_code}')
    except Exception as e:
        print(f'   Status: ERROR - {str(e)[:80]}')
else:
    print('2. NEWSAPI_KEY: NOT FOUND')

print()
