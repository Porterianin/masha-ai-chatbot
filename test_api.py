import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROK_API_KEY")  # Из .env

if not API_KEY:
    print("Ошибка: GROK_API_KEY не найден в .env! Проверь файл.")
    exit()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

data = {
    "messages": [
        {
            "role": "user",
            "content": "What is the meaning of life, the universe, and everything?"
        }
    ],
    "model": "grok-4",  # Как в curl
    "stream": False,
    "temperature": 0.7
}

response = requests.post(
    "https://api.x.ai/v1/chat/completions",
    headers=headers,
    json=data
)

print(f"Статус-код: {response.status_code}")
print("Полный ответ от сервера:")
print(response.text)

if response.status_code == 200:
    try:
        content = response.json()["choices"][0]["message"]["content"]
        print(f"Grok ответил: {content}")
    except KeyError as e:
        print(f"Ошибка в структуре ответа: {e}. Проверь response.text")
else:
    print(f"Ошибка API: Код {response.status_code}. Проверь ключ или кредиты.")