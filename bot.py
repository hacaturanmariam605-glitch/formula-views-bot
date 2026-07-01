import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Переменные окружения ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")

PREORDER_URL = os.environ.get("PREORDER_URL", "https://ваша-ссылка-на-форму")
ARTICLE_URL = os.environ.get("ARTICLE_URL", "https://teletype.in/@mariamrouze/formula")
COURSE_IMAGE_URL = os.environ.get("COURSE_IMAGE_URL")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS")
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Квиз-ответы")

# --- Вопросы квиза ---
QUESTIONS = [
    {
        "question": "Для чего важно выбирать конкретную известную личность?",
        "options": {
            "А": "Чем популярнее, тем больше просмотров",
            "Б": "Привлечь аудиторию по ценностям",
            "В": "Стать заметным для брендов"
        },
        "correct": "Б",
        "explanation": (
            "Выбор известной личности — это не просто про охваты, а про вашу аудиторию. "
            "Важно, чтобы её ценности совпадали с вашими, так вы привлекаете качественную аудиторию."
        )
    },
    {
        "question": "Можно ли комбинировать несколько формул в одном ролике?",
        "options": {
            "А": "Нет, они конфликтуют",
            "Б": "Да, это усиливает эффект",
            "В": "Да, но не больше двух"
        },
        "correct": "Б",
        "explanation": (
            "Да, использование нескольких формул делает ролик сильнее. "
            "Например, «ты + лайфхак + известная личность» будут удерживать и вовлекать зрителя эффективнее."
        )
    },
    {
        "question": "Почему формула «ты + актуальная тема» работает для новичков?",
        "options": {
            "А": "Алгоритмы продвигают новые аккаунты",
            "Б": "Актуальная тема сама цепляет внимание",
            "В": "Низкие затраты на производство"
        },
        "correct": "Б",
        "explanation": (
            "Актуальная тема сама по себе цепляет внимание, даже если вы новый блогер. "
            "Людям интересно мнение по животрепещущему вопросу, а не ваша популярность."
        )
    },
    {
        "question": "Что важнее: вирусный ролик или дисциплина?",
        "options": {
            "А": "Вирусный ролик — это охваты",
            "Б": "Дисциплина — стабильный рост",
            "В": "Оба важны, у каждого своя задача"
        },
        "correct": "В",
        "explanation": (
            "Вирусный ролик даёт быстрый всплеск, а дисциплина — стабильный рост. "
            "Я советую сочетать: системно работать над контентом и время от времени создавать "
            "потенциально вирусные видео. У каждого ролика своя задача."
        )
    }
]

# --- Сохранение в Google Sheets ---
def save_to_google_sheets(user_data, answers, score):
    try:
        if not GOOGLE_CREDENTIALS_JSON:
            logging.warning("Google Sheets не настроен — пропускаем сохранение.")
            return
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        try:
            sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        except gspread.SpreadsheetNotFound:
            sheet = client.create(GOOGLE_SHEET_NAME).sheet1
        if not sheet.get_all_records():
            headers = ["Дата", "User ID", "Имя", "Username", "Балл"] + [f"Вопрос {i+1}" for i in range(len(QUESTIONS))]
            sheet.append_row(headers)
        from datetime import datetime
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(user_data.get("id", "")),
            user_data.get("first_name", ""),
            user_data.get("username", ""),
            f"{score}/{len(QUESTIONS)}"
        ] + [answers.get(i, "") for i in range(len(QUESTIONS))]
        sheet.append_row(row)
        logging.info("Данные сохранены в Google Sheets")
    except Exception as e:
        logging.error(f"Ошибка при сохранении в Google Sheets: {e}")

# --- Обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name or "друг"
    text = (
        f"<b>Привет, {first_name}!</b> 👋\n"
        "Я подготовила для тебя статью, где ты найдёшь 5 простых формул для вирусного контента.\n\n"
        "Читай, сохраняй и сразу применяй — внутри информация, которую часто продают на платных курсах.\n\n"
        "А когда прочитаешь — возвращайся в бот и проходи тест, чтобы закрепить знания."
    )
    keyboard = [
        [InlineKeyboardButton("📖 Читать статью", url=ARTICLE_URL)],
        [InlineKeyboardButton("🧠 Пройти тест", callback_data="start_quiz")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_quiz":
        context.user_data["question_index"] = 0
        context.user_data["answers"] = {}
        await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get("question_index", 0)
    if idx >= len(QUESTIONS):
        await finish_quiz(update, context)
        return
    q = QUESTIONS[idx]
    text = f"<b>✨ Вопрос {idx+1} из {len(QUESTIONS)}</b>\n\n"
    text += f"{q['question']}\n\n"
    for key, value in q["options"].items():
        text += f"<b>{key}</b>) {value}\n"
    keyboard = [[InlineKeyboardButton(key, callback_data=f"ans_{key}") for key in q["options"].keys()]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_answer = query.data.split("_")[1]
    idx = context.user_data.get("question_index", 0)
    if idx >= len(QUESTIONS):
        return

    context.user_data["answers"][idx] = user_answer

    q = QUESTIONS[idx]
    correct = q["correct"]
    explanation = q["explanation"]

    if user_answer == correct:
        reply = f"🤍 <b>Верно!</b>\n\n📖 {explanation}"
    else:
        reply = f"💭 <b>Не совсем.</b>\n\n📖 {explanation}"

    await query.message.reply_text(reply, parse_mode='HTML')

    context.user_data["question_index"] = idx + 1
    if context.user_data["question_index"] >= len(QUESTIONS):
        await finish_quiz(update, context)
    else:
        await send_question(update, context)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data.get("answers", {})
    score = 0
    for i, q in enumerate(QUESTIONS):
        if answers.get(i) == q["correct"]:
            score += 1
    total = len(QUESTIONS)

    user = update.effective_user
    user_data = {
        "id": user.id,
        "first_name": user.first_name,
        "username": user.username
    }
    save_to_google_sheets(user_data, answers, score)

    praise = "Отличная работа, ты молодец! Теперь ты знаешь 5 формул, которые можешь применять в своих роликах."

    caption = (
        f"{praise}\n\n"
        "Если хочешь системно вести блог с пониманием, сотрудничать с брендами и понимать, "
        "какой формат контента для чего — оставь заявку на мини-курс <b>«OH MY BRAND»</b>.\n\n"
        "Заполняй анкету презаписи, чтобы сохранить за собой цену — <b>5 500 ₽</b> (вместо 10 000).\n"
        "Анкета ни к чему не обязывает."
    )

    keyboard = [[InlineKeyboardButton("📝 Предзапись на курс", url=PREORDER_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if COURSE_IMAGE_URL:
        await update.effective_chat.send_photo(
            photo=COURSE_IMAGE_URL,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.effective_chat.send_message(caption, reply_markup=reply_markup, parse_mode='HTML')

    context.user_data.clear()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — Начать и получить статью\n"
        "/help — Показать это сообщение"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^start_quiz$"))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern="^ans_"))
    logging.info("Бот запущен и слушает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
