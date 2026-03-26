import os
import requests
import time
from datetime import datetime

# ВСТАВЬ СЮДА
TOKEN = "8782638022:AAGIcj7aZipP5xNa7y26Xs3ah5h4YxE2yaI"
SUPABASE_KEY = "sb_publishable_S2ZI9GCQr5ZugXsXrpqPvw_y5UmnoQG"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
SUPABASE_URL = "https://dsbzlhemjgcayidwahgf.supabase.co"

expense_categories = {
    "Транспорт": ["Автобус/Метро", "Такси"],
    "Еда": ["Завтрак", "Обед", "Ужин", "Перекус", "для удовольствия"],
    "Обязательные": ["Аренда квартиры", "Ипотека", "Кредиты", "Стрижка", "Связь", "Спорт"],
    "Развлечения": ["Баня", "Заведения", "Горы/Парки/купание/кино", "Девушки"],
    "Одежда": ["Повседневная", "Классная"],
    "Подарки": ["Себе", "Другим"],
    "Здоровье": ["Приемы", "Анализы", "Таблетки", "Процедуры"],
    "Бытовые": ["Мыломойка", "Продукты", "Другое"],
    "Вредные привычки": ["Сигареты", "Шишки"]
}

last_update_id = None
user_states = {}

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    requests.post(BASE_URL + "/sendMessage", json=payload, verify=False)

def answer_callback_query(callback_query_id):
    requests.post(BASE_URL + "/answerCallbackQuery",
                  json={"callback_query_id": callback_query_id},
                  verify=False)

def get_cat1_keyboard():
    return {"inline_keyboard": [
        [{"text": cat1, "callback_data": f"cat1|{cat1}"}]
        for cat1 in expense_categories.keys()
    ]}

def get_cat2_keyboard(cat1):
    return {"inline_keyboard": [
        [{"text": cat2, "callback_data": f"cat2|{cat2}"}]
        for cat2 in expense_categories[cat1]
    ]}

def save_to_db(user_id, amount, category1, category2, comment):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "user_id": str(user_id),
        "expense_datetime": datetime.now().isoformat(),
        "amount": amount,
        "category1": category1,
        "category2": category2,
        "comment": comment
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/expenses",
        headers=headers,
        json=payload,
        verify=False
    )

    if resp.status_code not in (200, 201):
        raise Exception(resp.text)

print("Bot started...")

while True:
    try:
        params = {"timeout": 30}
        if last_update_id:
            params["offset"] = last_update_id

        updates = requests.get(BASE_URL + "/getUpdates", params=params, verify=False).json()

        for update in updates.get("result", []):
            last_update_id = update["update_id"] + 1

            if "callback_query" in update:
                cq = update["callback_query"]
                chat_id = cq["message"]["chat"]["id"]
                data = cq["data"]

                answer_callback_query(cq["id"])

                state = user_states.setdefault(chat_id, {})

                if data.startswith("cat1|"):
                    cat1 = data.split("|")[1]
                    state["category1"] = cat1
                    state["step"] = "cat2"

                    send_message(chat_id, "Выбери категорию 2",
                                 get_cat2_keyboard(cat1))

                elif data.startswith("cat2|"):
                    cat2 = data.split("|")[1]
                    state["category2"] = cat2
                    state["step"] = "comment"

                    send_message(chat_id, "Комментарий или '-'")

            elif "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "").strip()

                state = user_states.setdefault(chat_id, {})

                if text == "/start":
                    state.clear()
                    state["step"] = "amount"
                    send_message(chat_id, "Введи сумму")
                    continue

                if state.get("step") == "amount":
                    try:
                        state["amount"] = float(text)
                        state["step"] = "cat1"

                        send_message(chat_id, "Выбери категорию",
                                     get_cat1_keyboard())
                    except:
                        send_message(chat_id, "Введи число")

                elif state.get("step") == "comment":
                    comment = "" if text == "-" else text

                    try:
                        save_to_db(
                            chat_id,
                            state["amount"],
                            state["category1"],
                            state["category2"],
                            comment
                        )

                        send_message(chat_id, "✅ Сохранено\n/start для новой записи")
                    except Exception as e:
                        send_message(chat_id, f"Ошибка: {e}")

                    state.clear()

    except Exception as e:
        print("Error:", e)

    time.sleep(1)