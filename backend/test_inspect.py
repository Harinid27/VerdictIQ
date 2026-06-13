import inspect
import google.generativeai as genai
print(inspect.signature(genai.GenerativeModel.__init__))
