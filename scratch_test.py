import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyDXaNm4G9DcZh_fPPFF8db0GqqIGdgvsqs")

model = genai.GenerativeModel('gemini-1.5-pro-latest')

prompt = "Please summarize exactly what the speaker says in this video: https://www.youtube.com/watch?v=F-wZLl-LSMA"

try:
    response = model.generate_content(prompt)
    print("Gemini response:")
    print(response.text)
except Exception as e:
    print("Error:", e)
