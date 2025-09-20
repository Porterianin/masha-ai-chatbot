from supabase import create_client, AsyncClient
import requests
import os
import json
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Ошибка: SUPABASE_URL или SUPABASE_KEY не найдены!")
    exit()

supabase: AsyncClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# Grok API
GROK_API_KEY = os.getenv("GROK_API_KEY")
if not GROK_API_KEY:
    print("Ошибка: GROK_API_KEY не найден!")
    exit()

# Функции Supabase
async def get_personality(personality_id=1):
    response = await supabase.from_("personality").select("*").eq("id", personality_id).execute()
    return response.data[0] if response.data else {}

async def get_memories(personality_id=1):
    response = await supabase.from_("memory").select("fact").eq("personality_id", personality_id).execute()
    return [row["fact"] for row in response.data] if response.data else []

async def get_interactions_with_other(personality_id=1, other_personality_id=None):
    query = supabase.from_("interactions").select("user_input, response").eq("personality_id", personality_id)
    if other_personality_id:
        query = query.eq("other_personality_id", other_personality_id)
    response = await query.execute()
    return [(row["user_input"], row["response"]) for row in response.data] if response.data else []

async def add_memory(personality_id, fact):
    await supabase.from_("memory").insert({"personality_id": personality_id, "fact": fact}).execute()

async def add_interaction(personality_id, user_input, response, other_personality_id=None):
    await supabase.from_("interactions").insert({
        "personality_id": personality_id,
        "other_personality_id": other_personality_id,
        "user_input": user_input,
        "response": response,
        "interaction_type": "character_interaction" if other_personality_id else "user_conversation"
    }).execute()

# Grok API
async def get_grok_response(user_input, personality, memories, other_personality_id=None):
    other_personality = await get_personality(other_personality_id) if other_personality_id else personality
    interactions = await get_interactions_with_other(personality['id'], other_personality_id) if other_personality_id else []
    other_info = (
        f"Ты говоришь с {other_personality['name']}. Её черты: {json.dumps(other_personality.get('traits', {}))}. "
        f"Её история: {other_personality.get('backstory', 'неизвестно')}. "
        f"Прошлые разговоры с ней: {', '.join([f'{i[0]} -> {i[1][:30]}...' for i in interactions])}."
    ) if other_personality_id else ""
    prompt = (
        f"Ты Маша, 18-летняя студентка. Твои черты: {json.dumps(personality['traits'])}. "
        f"Твоя история: {personality['backstory']}. Воспоминания: {', '.join(memories[-5:])}." 
        f"{other_info} Общайся как живая девушка: весёлая, саркастичная, с эмодзи. На русском. "
        f"Не повторяй базовые факты. Ответь на: {user_input}"
    )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROK_API_KEY}"},
        json={"messages": [{"role": "user", "content": prompt}], "model": "grok-4", "stream": False, "temperature": 0.7}
    ))
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"API ошибка: {response.status_code}, {response.text}")
        return f"Ой, ошибка API: {response.status_code}. Проверь кредиты! 😅"

# Realtime подписка
async def listen_realtime():
    try:
        print("Запускаем Realtime-подписку...")
        channel_memory = supabase.realtime.channel("public:memory")
        channel_memory.on("INSERT", lambda payload: print(f"Новое воспоминание: {payload['record']['fact']}"))
        await channel_memory.subscribe()
        print("Подписка на memory установлена")

        channel_interactions = supabase.realtime.channel("public:interactions")
        channel_interactions.on("INSERT", lambda payload: print(f"Новый чат: {payload['record']['user_input']} -> {payload['record']['response'][:30]}..."))
        await channel_interactions.subscribe()
        print("Подписка на interactions установлена")

        # Активно слушаем события
        while True:
            await asyncio.sleep(1)
            print("Ожидаем Realtime-события...")
    except Exception as e:
        print(f"Ошибка Realtime: {str(e)}")

# Основной чат
async def main():
    personality = await get_personality(1)
    if not personality:
        print("Ошибка: Маша не найдена!")
        return
    memories = await get_memories(1)
    print(f"Привет! Я Маша, {personality['traits']['age']} лет. Давай болтать? (упомяни 'Катя' для разговора с ней, exit для выхода)")

    # Запускаем Realtime в фоне
    loop = asyncio.get_event_loop()
    loop.create_task(listen_realtime())

    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "Ты: ")
        user_input = user_input.strip()
        if user_input.lower() == 'exit':
            print("Маша: Пока! Было весело 😘")
            break
        other_personality_id = 2 if "катя" in user_input.lower() else None
        response = await get_grok_response(user_input, personality, memories, other_personality_id)
        print(f"Маша: {response}")
        await add_memory(1, f"Разговор: {user_input} -> {response[:50]}...")
        await add_interaction(1, user_input, response, other_personality_id)
        memories = await get_memories(1)

if __name__ == "__main__":
    asyncio.run(main())