import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  data=json.dumps({
    "model": "deepseek/deepseek-chat-v3.1:free",
    "messages": [
      {
        "role": "user",
        "content": "hello , my name is ibrahim "
      }
    ],
    
  })
)
# Extract answer
if response.status_code == 200:
    result = response.json()
    message = result["choices"][0]["message"]["content"]
    print("Bot reply:", message)