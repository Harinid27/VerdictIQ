import google.generativeai as genai
try:
    model = genai.GenerativeModel('gemini-2.5-flash', api_key='dummy_key')
    print("SUCCESS: api_key parameter is accepted by GenerativeModel constructor!")
except Exception as e:
    print("FAILED:", e)
