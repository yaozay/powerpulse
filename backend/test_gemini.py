import os, sys
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

KEY = os.getenv("GEMINI_API_KEY")
assert KEY, "Missing GEMINI_API_KEY in .env"
genai.configure(api_key=KEY)

# See what's available in your SDK
print("Listing models that support generateContent:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(" -", m.name)

MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
print("Using model:", MODEL)

model = genai.GenerativeModel(MODEL)
resp = model.generate_content("Say hello from PowerPulse in 5 words.")
print("Response:", resp.text or "(no .text)")
