import requests
import time
from datetime import datetime

# ВСТАВЛЕНО КАК ВЧЕРА (БЕЗ RAILWAY)
TOKEN = "8782638022:AAGIcj7aZipP5xNa7y26Xs3ah5h4YxE2yaI"
SUPABASE_KEY = "sb_publishable_S2ZI9GCQr5ZugXsXrpqPvw_y5UmnoQG"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
SUPABASE_URL = "https://dsbzlhemjgcayidwahgf.supabase.co"

# --- КАТЕГОРИИ РАСХОДОВ ---
expense_categories = {
    "Транспорт": ["Автобус/Метро", "Такси"],
    "Еда": ["Завтрак", "Обед", "Ужин", "Перекус", "для удовольствия"],
    "Обязательные": ["Аренда квартиры", "Ипотека", "Кредиты", "Стрижка", "Связь", "Спорт"],
    "Развлечения": ["Баня", "Заведения", "Горы/Парки/купание/кино"],
    "Одежда": ["Повседневная", "Классная"],
    "Подарки": ["Себе", "Другим"],
    "Здоровье": ["Приемы", "Анализы", "Таблетки", "Процедуры"],
    "Бытовые": ["Бытовая химия", "Продукты", "Другое"],
    "Вредные привычки": ["Сигареты", "Шишки"]
}

# --- КАТЕГОРИИ ТРЕНИРОВОК ---
workout_categories = {
    "Спина": ["Турник широким хватом", "Гиперэкстензия", "Тяга в наклоне", "Гребля"],
    "Ноги": ["Выпады", "Присед", "Болгарский присед", "Жим ногами", "Икры", "Разгибания", "Сгибания"],
    "Грудь": ["Жим лежа", "Жим лежа на наклонной", "Тренажер"],
    "Плечи": ["Армейский", "Подъем штанги", "Разведения"],
    "Трицепс": ["Брусья", "Жим узким хватом", "Косичка", "Прямой велик", "Гантеля из за головы"],
    "Бицепс": ["Сидя тренажер", "Штанга", "Молот", "Косичка", "Турник обратным хватом"]
}

last_update_id = None
user_states = {}

# --- ОБЩИЕ ФУНКЦИИ ---
def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(BASE_URL + "/sendMessage", json=payload, verify=False)

def answer_callback_query(callback_query_id):
    requests.post(
        BASE_URL + "/answerCallbackQuery",
        json={"callback_query_id": callback_query_id},
        verify=False
    )

# --- КЛАВИАТУРЫ ---
def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "💰 Расходы", "callback_data": "mode|expense"}],
            [{"text": "🏋️ Тренировки", "callback_data": "mode|workout"}]
        ]
    }

def get_cat1_keyboard(categories):
    return {
        "inline_keyboard": [
            [{"text": c, "callback_data": f"cat1|{c}"}]
            for c in categories.keys()
        ]
    }

def get_cat2_keyboard(categories, cat1):
    return {
        "inline_keyboard": [
            [{"text": c, "callback_data": f"cat2|{c}"}]
            for c in categories[cat1]
        ]
    }

# --- СОХРАНЕНИЕ ---
def save_expense(user_id, first_name, amount, cat1, cat2, comment):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "user_id": str(user_id),
        "first_name": first_name,
        "expense_datetime": datetime.now().isoformat(),
        "amount": amount,
        "category1": cat1,
        "category2": cat2,
        "comment": comment
    }

    requests.post(
        f"{SUPABASE_URL}/rest/v1/expenses",
        headers=headers,
        json=payload,
        verify=False
    )

def save_workout(user_id, first_name, cat1, cat2, weight, reps, comment):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "user_id": str(user_id),
        "first_name": first_name,
        "workout_datetime": datetime.now().isoformat(),
        "category1": cat1,
        "category2": cat2,
        "weight": weight,
        "reps": reps,
        "comment": comment
    }

    requests.post(
        f"{SUPABASE_URL}/rest/v1/workouts",
        headers=headers,
        json=payload,
        verify=False
    )

print("Bot started...")

while True:
    try:
        params = {"timeout": 30}
        if last_update_id:
            params["offset"] = last_update_id

        updates = requests.get(BASE_URL + "/getUpdates", params=params, verify=False).json()

        for update in updates.get("result", []):
            last_update_id = update["update_id"] + 1

            # --- CALLBACK ---
            if "callback_query" in update:
                cq = update["callback_query"]
                chat_id = cq["message"]["chat"]["id"]
                data = cq["data"]

                answer_callback_query(cq["id"])

                state = user_states.setdefault(chat_id, {})

                if data.startswith("mode|"):
                    mode = data.split("|")[1]
                    state["mode"] = mode
                    state["step"] = "cat1"

                    categories = expense_categories if mode == "expense" else workout_categories

                    send_message(chat_id, "Выбери категорию", get_cat1_keyboard(categories))

                elif data.startswith("cat1|"):
                    cat1 = data.split("|")[1]
                    state["category1"] = cat1
                    state["step"] = "cat2"

                    categories = expense_categories if state["mode"] == "expense" else workout_categories

                    send_message(chat_id, "Выбери подкатегорию", get_cat2_keyboard(categories, cat1))

                elif data.startswith("cat2|"):
                    cat2 = data.split("|")[1]
                    state["category2"] = cat2

                    if state["mode"] == "expense":
                        state["step"] = "amount"
                        send_message(chat_id, "Введи сумму")
                    else:
                        state["step"] = "weight"
                        send_message(chat_id, "Введи вес")

            # --- MESSAGE ---
            elif "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()
                first_name = msg.get("from", {}).get("first_name", "")

                state = user_states.setdefault(chat_id, {})

                if text == "/start":
                    state.clear()
                    send_message(chat_id, f"Привет, {first_name} 👋\nЧто записать?", main_menu())
                    continue

                if state.get("mode") == "expense":
                    if state.get("step") == "amount":
                        state["amount"] = float(text)
                        state["step"] = "comment"
                        send_message(chat_id, "Комментарий или '-'")

                    elif state.get("step") == "comment":
                        comment = "" if text == "-" else text

                        save_expense(
                            chat_id, first_name,
                            state["amount"],
                            state["category1"],
                            state["category2"],
                            comment
                        )

                        send_message(chat_id, "✅ Сохранено")
                        state.clear()

                elif state.get("mode") == "workout":
                    if state.get("step") == "weight":
                        state["weight"] = float(text)
                        state["step"] = "reps"
                        send_message(chat_id, "Повторы")

                    elif state.get("step") == "reps":
                        state["reps"] = int(text)
                        state["step"] = "comment"
                        send_message(chat_id, "Комментарий или '-'")

                    elif state.get("step") == "comment":
                        comment = "" if text == "-" else text

                        save_workout(
                            chat_id, first_name,
                            state["category1"],
                            state["category2"],
                            state["weight"],
                            state["reps"],
                            comment
                        )

                        send_message(chat_id, "🏋️ Сохранено")
                        state.clear()

    except Exception as e:
        print("Error:", e)

    time.sleep(1)
