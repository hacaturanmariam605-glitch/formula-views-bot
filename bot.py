import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Переменные окружения ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан!")

PREORDER_URL = os.environ.get("PREORDER_URL", "https://ваша-ссылка-на-форму")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS")  # содержимое json-файла сервисного аккаунта
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Квиз-ответы")

# --- Вопросы квиза ---
QUESTIONS = [
    {
        "question": "Для чего важно выбирать конкретную известную личность для коллаборации?",
        "options": {
            "А": "Чтобы получить больше просмотров за счёт её популярности",
            "Б": "Чтобы привлечь ту аудиторию, которая разделяет ваши ценности и подходит вашему блогу",
            "В": "Чтобы повысить качество монтажа и продакшена",
            "Г": "Чтобы бренды быстрее заметили ваш аккаунт"
        },
        "correct": "Б"
    },
    {
        "question": "Можно ли в одном ролике комбинировать несколько формул из статьи?",
        "options": {
            "А": "Нет, каждая формула должна использоваться отдельно, иначе они конфликтуют",
            "Б": "Да, например, можно соединить «ты + лайфхаки/польза» с триггером «известная личность» для усиления эффекта",
            "В": "Да, но только если комбинировать не больше двух формул",
            "Г": "Нет, формулы придуманы для разных ниш и несовместимы"
        },
        "correct": "Б"
    },
    {
        "question": "Почему формула «ты + актуальная тема» работает даже для начинающих блогеров?",
        "options": {
            "А": "Потому что алгоритмы Instagram продвигают только новые аккаунты",
            "Б": "Потому что аудитории интересна сама тема, даже если блогер пока неизвестен",
            "В": "Потому что она требует минимальных затрат на производство",
            "Г": "Потому что так можно быстро набрать 10 000 подписчиков"
        },
        "correct": "Б"
    },
    {
        "question": "Какая ошибка чаще всего мешает получить результат от коллаборации с известной личностью?",
        "options": {
            "А": "Выбирать только самых популярных блогеров, не учитывая их аудиторию",
            "Б": "Делать коллаборацию только один раз и ждать мгновенного взрыва",
            "В": "Не добавлять личный опыт и пользу в ролик с этой личностью",
            "Г": "Всё перечисленное"
        },
        "correct": "Г"
    },
    {
        "question": "Почему системный подход и дисциплина важнее, чем один «вирусный» ролик?",
        "options": {
            "А": "Потому что один вирусный ролик не даёт стабильного роста и доверия аудитории",
            "Б": "Потому что алгоритмы любят регулярность и предсказуемость",
            "В": "Потому что системный подход позволяет тестировать гипотезы и масштабировать успех",
            "Г": "Всё перечисленное"
        },
        "correct": "Г"
    }
]

# --- Функция для сохранения в Google Sheets ---
def save_to_google_sheets(user_data, answers, score):
    try:
        if not GOOGLE_CREDENTIALS_JSON:
            logging.warning("Google Sheets не настроен — пропускаем сохранение.")
            return
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Открываем или создаём таблицу
        try:
            sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        except gspread.SpreadsheetNotFound:
            sheet = client.create(GOOGLE_SHEET_NAME).sheet1
            # Даём доступ редактору (можно добавить свой email)
            # sheet.add_editor('ваш-email@gmail.com')  # раскомментируйте, если нужно
        # Если таблица пуста, добавляем заголовки
        if not sheet.get_all_records():
            headers = ["Дата", "User ID", "Имя", "Username", "Балл"] + [f"Вопрос {i+1}" for i in range(len(QUESTIONS))]
            sheet.append_row(headers)
        # Формируем строку для записи
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
        f"Привет, {first_name}!\n"
        "Держи статью — «Формула просмотров»:\n"
        "https://teletype.in/@mariamrouze/formula\n\n"
        "Внутри — информация, которую часто продают на платных курсах. "
        "Читай, сохраняй и сразу применяй.\n"
        "👇 А после прочтения жми на кнопку — я дам тебе задание, "
        "которое поможет внедрить формулы уже сегодня."
    )
    keyboard = [[InlineKeyboardButton("✅ Я прочитал(а) статью", callback_data="read_article")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "read_article":
        # Инициализируем состояние пользователя
        context.user_data["question_index"] = 0
        context.user_data["answers"] = {}
        await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get("question_index", 0)
    if idx >= len(QUESTIONS):
        # Квиз завершён
        await finish_quiz(update, context)
        return
    q = QUESTIONS[idx]
    text = f"❓ Вопрос {idx+1} из {len(QUESTIONS)}:\n{q['question']}\n\n"
    for key, value in q["options"].items():
        text += f"{key}) {value}\n"
    text += "\nНапиши букву ответа (А, Б, В или Г):"
    await update.callback_query.edit_message_text(text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, идёт ли сейчас квиз
    if "question_index" not in context.user_data:
        # Игнорируем сообщения, если квиз не активен
        await update.message.reply_text("Чтобы начать квиз, нажми /start и прочитай статью, затем нажми кнопку.")
        return

    user_answer = update.message.text.strip().upper()
    valid_keys = ["А", "Б", "В", "Г"]
    if user_answer not in valid_keys:
        await update.message.reply_text("Пожалуйста, ответь одной из букв: А, Б, В или Г.")
        return

    idx = context.user_data.get("question_index", 0)
    if idx >= len(QUESTIONS):
        return

    # Сохраняем ответ
    context.user_data["answers"][idx] = user_answer

    # Проверяем правильность
    correct = QUESTIONS[idx]["correct"]
    if user_answer == correct:
        reply = "✅ Верно!"
    else:
        reply = f"❌ Не совсем. Правильный ответ: {correct}"

    # Увеличиваем индекс и отправляем следующий вопрос или завершаем
    context.user_data["question_index"] = idx + 1
    await update.message.reply_text(reply)

    if context.user_data["question_index"] >= len(QUESTIONS):
        await finish_quiz(update, context)
    else:
        await send_next_question(update, context)

async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get("question_index", 0)
    if idx >= len(QUESTIONS):
        await finish_quiz(update, context)
        return
    q = QUESTIONS[idx]
    text = f"❓ Вопрос {idx+1} из {len(QUESTIONS)}:\n{q['question']}\n\n"
    for key, value in q["options"].items():
        text += f"{key}) {value}\n"
    text += "\nНапиши букву ответа (А, Б, В или Г):"
    await update.message.reply_text(text)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Подсчёт баллов
    answers = context.user_data.get("answers", {})
    score = 0
    for i, q in enumerate(QUESTIONS):
        if answers.get(i) == q["correct"]:
            score += 1
    total = len(QUESTIONS)

    # Сохраняем в Google Sheets
    user = update.effective_user
    user_data = {
        "id": user.id,
        "first_name": user.first_name,
        "username": user.username
    }
    save_to_google_sheets(user_data, answers, score)

    # Итоговое сообщение
    if score == total:
        stars = "🌟 Отлично! Ты настоящий эксперт!"
    elif score >= total - 1:
        stars = "🔥 Очень хорошо! Почти всё правильно!"
    elif score >= total // 2:
        stars = "👍 Неплохо! Есть куда расти."
    else:
        stars = "📖 Стоит перечитать статью внимательнее."

    final_text = (
        f"🎯 Ты набрал(а) {score} из {total}!\n"
        f"{stars}\n\n"
        "Если хочешь разобрать формулы глубже и получить готовую систему под свой блог — "
        "оставь заявку на мини-курс «OH MY BRAND»:\n"
        f"{PREORDER_URL}\n\n"
        "Цена для участников квиза — 5 500 ₽ (вместо 10 000).\n"
        "Анкета ни к чему не обязывает."
    )
    await update.message.reply_text(final_text)

    # Очищаем состояние, чтобы не мешать
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
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logging.info("Бот запущен и слушает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
