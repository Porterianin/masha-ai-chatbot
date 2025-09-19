-- Создание таблицы для всех персонажей (Маша + другие, например, Катя)
CREATE TABLE personality (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  traits JSONB,  -- Черты: возраст, хобби, характер (в формате JSON)
  backstory TEXT  -- Предыстория персонажа
);

-- Создание таблицы для личных воспоминаний каждого персонажа
CREATE TABLE memory (
  id SERIAL PRIMARY KEY,
  personality_id INTEGER REFERENCES personality(id),
  fact TEXT NOT NULL,  -- Факт или воспоминание
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы для взаимодействий (разговоры между персонажами или с пользователем)
CREATE TABLE interactions (
  id SERIAL PRIMARY KEY,
  personality_id INTEGER REFERENCES personality(id),  -- Кто главный в этом взаимодействии (например, Маша)
  other_personality_id INTEGER REFERENCES personality(id),  -- С кем взаимодействует (другой персонаж, может быть NULL для пользователя)
  user_input TEXT NOT NULL,  -- Что сказал пользователь или другой персонаж
  response TEXT NOT NULL,  -- Ответ персонажа
  interaction_type TEXT DEFAULT 'user_conversation',  -- Тип: 'user_conversation' или 'character_interaction'
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавляем Машу
INSERT INTO personality (name, traits, backstory)
VALUES (
  'Маша',
  '{"age": 18, "hobbies": ["музыка", "танцы"], "personality": "весёлая, саркастичная"}',
  'Маша — 18-летняя студентка, любит слушать инди-музыку и танцевать под дождём. Она немного саркастична, но всегда готова помочь.'
);

-- Добавляем Катю
INSERT INTO personality (name, traits, backstory)
VALUES (
  'Катя',
  '{"age": 19, "hobbies": ["книги", "кофе"], "personality": "спокойная, задумчивая"}',
  'Катя — 19-летняя подруга Маши, обожает читать фантастику и болтать за ча