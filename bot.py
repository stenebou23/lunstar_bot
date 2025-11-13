# bot.py — LUNSTAR Bot
import telebot
import json
import random
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


# ---------------- CONFIG ----------------
TOKEN = "8241297349:AAHrmit98ZyQwKsuSqQbwicIolBjsvS01Hw"
DATA_FILES = {
    "Экономика промышленности": "industry_economics.json",
    "Инновационная экономика": "innovation_economics.json",
    "Макроэкономика": "macroeconomics.json"
}
RESULTS_FILE = "results.json"
# ----------------------------------------


bot = telebot.TeleBot(TOKEN)
state = {}


# 🗂️ Загружаем старые результаты (если есть)
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results_db = json.load(f)
else:
    results_db = {}


def save_results():
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results_db, f, ensure_ascii=False, indent=2)


def load_questions(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


# 🎛 Главное меню
def keyboard_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎓 Обучение", "🧩 Тест")
    kb.add("🏆 Результаты")
    return kb


# 📚 Меню предметов
def keyboard_subjects():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for name in DATA_FILES.keys():
        kb.add(name)
    kb.add("⬅️ Назад")
    return kb


# ➡️ Кнопки перехода
def keyboard_next():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➡️ Далее")
    kb.add("⏹️ Выход")
    return kb


# ----------------- БЛОК ОБРАБОТКИ -------------------


@bot.message_handler(commands=["start", "help"])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "🔥 Это LUNSTAR BOT!\n\n🎓 Учись, тестируйся! \n\nВыбирай режим 👇",
        reply_markup=keyboard_main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🎓 Обучение")
def handle_learn(message):
    state[message.chat.id] = {"mode": "learn"}
    bot.send_message(message.chat.id, "📘 Выбери предмет:", reply_markup=keyboard_subjects())


@bot.message_handler(func=lambda m: m.text == "🧩 Тест")
def handle_test(message):
    state[message.chat.id] = {"mode": "test"}
    bot.send_message(message.chat.id, "📗 Выбери предмет:", reply_markup=keyboard_subjects())


@bot.message_handler(func=lambda m: m.text == "🏆 Результаты")
def handle_results(message):
    uid = str(message.chat.id)
    user_res = results_db.get(uid, {})
    if not user_res:
        bot.send_message(message.chat.id, "😎 Пока нет результатов.", reply_markup=keyboard_main_menu())
        return
    txt = "🏆 Твои результаты:\n\n"
    for subj, score in user_res.items():
        txt += f"📘 {subj}: {score} правильных\n"
    bot.send_message(message.chat.id, txt, reply_markup=keyboard_main_menu())


@bot.message_handler(func=lambda m: m.text in DATA_FILES.keys())
def handle_subject(message):
    chat = message.chat.id
    mode = state.get(chat, {}).get("mode")
    if not mode:
        bot.send_message(chat, "Выбери режим сначала.", reply_markup=keyboard_main_menu())
        return
    subject = message.text
    questions = load_questions(DATA_FILES[subject])
    random.shuffle(questions)
    state[chat].update({
        "subject": subject,
        "questions": questions,
        "index": 0,
        "score": 0
    })
    if mode == "learn":
        send_learning(chat)
    else:
        send_test(chat)


# --------- 🎓 ОБУЧЕНИЕ ----------
def send_learning(chat):
    s = state[chat]
    idx = s["index"]
    qs = s["questions"]
    if idx >= len(qs):
        bot.send_message(chat, "🎓 Обучение завершено! 💯", reply_markup=keyboard_main_menu())
        del state[chat]
        return
    q = qs[idx]
    ans = q["options"][q["answer_index"]]
    text = f"💭 Вопрос {idx + 1}/{len(qs)}:\n\n❓ {q['question']}\n✅ Ответ: {ans}"
    bot.send_message(chat, text)
    s["index"] += 1
    bot.send_message(chat, "➡️ Далее", reply_markup=keyboard_next())


# --------- 🧩 ТЕСТ ----------
def send_test(chat):
    s = state[chat]
    idx = s["index"]
    qs = s["questions"]
    if idx >= len(qs):
        uid = str(chat)
        subj = s["subject"]
        results_db.setdefault(uid, {})
        results_db[uid][subj] = s["score"]
        save_results()
        bot.send_message(chat, f"✅ Тест завершён!\n📊 Результат: {s['score']}/{len(qs)}", reply_markup=keyboard_main_menu())
        del state[chat]
        return


    q = qs[idx]
    options = q["options"][:]
    random.shuffle(options)
    s["correct"] = q["options"][q["answer_index"]]
    s["options"] = options


    text = f"🧩 Вопрос {idx + 1}/{len(qs)}\n\n❓ {q['question']}\n\n"
    for i, o in enumerate(options):
        text += f"{chr(65 + i)}) {o}\n"
    text += "\nВыбери A / B / C / D 👇"


    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("A", "B", "C", "D")
    kb.add("⏹️ Выход")
    bot.send_message(chat, text, reply_markup=kb)


# --------- 💬 ОТВЕТЫ ----------
@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    chat = message.chat.id
    if chat not in state:
        bot.send_message(chat, "💬 Напиши /start чтобы начать.", reply_markup=keyboard_main_menu())
        return


    if message.text == "⏹️ Выход":
        bot.send_message(chat, "⬅️ Возвращаю в главное меню.", reply_markup=keyboard_main_menu())
        del state[chat]
        return


    s = state[chat]


    # 🎓 Обучение
    if s["mode"] == "learn":
        if message.text == "➡️ Далее":
            send_learning(chat)
        elif message.text == "⏹️ Выход":
            bot.send_message(chat, "⬅️ Возвращаю в главное меню.", reply_markup=keyboard_main_menu())
            del state[chat]
        else:
            bot.send_message(chat, "Нажми '➡️ Далее' или '⏹️ Выход'")


    # 🧩 Тест
    elif s["mode"] == "test":
        text = message.text.strip().upper()
        if text not in ["A", "B", "C", "D"]:
            bot.send_message(chat, "Выбери вариант: A / B / C / D 👇")
            return


        i = ord(text) - 65
        chosen = s["options"][i] if i < len(s["options"]) else None


        if chosen == s["correct"]:
            s["score"] += 1
            bot.send_message(chat, "✅ Верно! 🔥")
        else:
            bot.send_message(chat, f"❌ Неа, правильный ответ:\n👉 {s['correct']}")


        s["index"] += 1
        send_test(chat)


print("✅ Бот запущен и готов к работе 🔥")
bot.infinity_polling()