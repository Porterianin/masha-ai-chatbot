import streamlit as st
from supabase import create_client
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Grok API
GROK_API_KEY = os.getenv("GROK_API_KEY")

# Функции Supabase
def get_personality(personality_id=1):
    response = supabase.table("personality").select("*").eq("id", personality_id).execute()
    return response.data[0] if response.data else {}

def get_memories(personality_id=1):
    response = supabase.table("memory").select("fact").eq("personality_id", personality_id).execute()
    return [row["fact"] for row in response.data]

def get_interactions_with_other(personality_id=1, other_personality_id=None):
    query = supabase.table("interactions").select("user_input, response").eq("personality_id", personality_id)
    if other_personality_id:
        query = query.eq("other_personality_id", other_personality_id)
    response = query.execute()
    return [(row["user_input"], row["response"]) for row in response.data]

def add_memory(personality_id, fact):
    supabase.table("memory").insert({"personality_id": personality_id, "fact": fact}).execute()

def add_interaction(personality_id, user_input, response, other_personality_id=None):
    supabase.table("interactions").insert({
        "personality_id": personality_id,
        "other_personality_id": other_personality_id,
        "user_input": user_input,
        "response": response,
        "interaction_type": "character_interaction" if other_personality_id else "user_conversation"
    }).execute()

# Grok API
def get_grok_response(user_input, personality, memories, other_personality_id=None):
    other_personality = get_personality(other_personality_id) if other_personality_id else {}
    other_info = (
        f"Ты говоришь с {other_personality['name']}. Её черты: {json.dumps(other_personality.get('traits', {}))}. "
        f"Её история: {other_personality.get('backstory', 'неизвестно')}. "
        f"Прошлые разговоры с ней: {', '.join([f'{i[0]} -> {i[1][:30]}...' for i in get_interactions_with_other(personality['id'], other_personality_id)])}."
    ) if other_personality else ""
    prompt = (
        f"Ты Маша, 18-летняя студентка. Твои черты: {json.dumps(personality['traits'])}. "
        f"Твоя история: {personality['backstory']}. Воспоминания: {', '.join(memories[-5:])}." 
        f"{other_info} Общайся как живая девушка: весёлая, саркастичная, с эмодзи. На русском. "
        f"Не повторяй базовые факты. Ответь на: {user_input}"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "grok-4",
        "stream": False,
        "temperature": 0.7
    }
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ой, ошибка API: {response.status_code}. Проверь кредиты! 😅"

# Streamlit интерфейс
st.title("Чат с Машей")
st.write("Общайтесь с Машей, упомяните 'Катя' для разговора о ней!")

# Инициализация сессии
if 'messages' not in st.session_state:
    st.session_state.messages = []
    personality = get_personality(1)
    if personality:
        st.session_state.messages.append({"role": "assistant", "content": f"Привет! Я Маша, {personality['traits']['age']} лет. Давай болтать? 😏"})

# Отображение сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод пользователя
user_input = st.chat_input("Ты: ")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Получаем ответ
    personality = get_personality(1)
    memories = get_memories(1)
    other_personality_id = 2 if "катя" in user_input.lower() else None
    response = get_grok_response(user_input, personality, memories, other_personality_id)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

    # Сохраняем в базу
    add_memory(1, f"Разговор: {user_input} -> {response[:50]}...")
    add_interaction(1, user_input, response, other_personality_id)