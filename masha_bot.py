from supabase import create_client
import requests
import json

# Настройки Supabase (замени на свои ключи из supabase_keys.txt)
SUPABASE_URL = "https://bvojjnipdrnjbelanjqs.supabase.co"  # Например, https://xyz.supabase.co
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2b2pqbmlwZHJuamJlbGFuanFzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyNTQzNzQsImV4cCI6MjA3MzgzMDM3NH0.pyOX6bS-8lJCijDPwhCvzqzgLdFadDULL4J3UTL5EE8"  # Например, eyJhb...

# Инициализация Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Функция: Получить данные о Маше
def get_personality(personality_id=1):
    response = supabase.table("personality").select("*").eq("id", personality_id).execute()
    return response.data[0] if response.data else {}

# Функция: Получить воспоминания Маши
def get_memories(personality_id=1):
    response = supabase.table("memory").select("fact").eq("personality_id", personality_id).execute()
    return [row["fact"] for row in response.data]

# Функция: Добавить новое воспоминание
def add_memory(personality_id, fact):
    supabase.table("memory").insert({"personality_id": personality_id, "fact": fact}).execute()

# Функция: Добавить взаимодействие (разговор)
def add_interaction(personality_id, user_input, response, other_personality_id=None):
    supabase.table("interactions").insert({
        "personality_id": personality_id,
        "other_personality_id": other_personality_id,
        "user_input": user_input,
        "response": response,
        "interaction_type": "user_conversation"
    }).execute()

# Функция: Отправить запрос в Grok API
def get_grok_response(user_input, personality, memories):
    prompt = (
        f"Ты Маша, 18-летняя студентка. Твои черты: {json.dumps(personality['traits'])}. "
        f"Твоя история: {personality['backstory']}. Воспоминания: {memories}. "
        f"Отвечай как живая девушка, весёлая и саркастичная, на русском. "
        f"Вот что тебе сказали konsekw: написали: {user_input}"
    )
    headers = {"Authorization": "Bearer ТВОЙ_GROK_API_KEY"}  # Замени на ключ API
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers,
        json={
            "model": "grok-4",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# Основная функция: Обработка разговора
def main():
    # Получаем данные Маши
    personality = get_personality(1)
    memories = get_memories(1)
    print(f"Маша: {personality['name']}, черты: {personality['traits']}")

    # Пример разговора
    user_input = input("Ты: ")
    response = get_grok_response(user_input, personality, memories)
    print(f"Маша: {response}")

    # Сохраняем разговор
    add_memory(1, f"Пользователь сказал: {user_input}")
    add_interaction(1, user_input, response)

if __name__ == "__main__":
    main()