import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
 # Optional. Site title for rankings on openrouter.ai.
  },
  data=json.dumps({
    "model": "tngtech/deepseek-r1t2-chimera:free",
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ],
    
  })
)
print(response.status_code, response.text)  
