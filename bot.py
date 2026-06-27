import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TELEGRAM_TOKEN не установлена!")

# ССЫЛКИ
ARTICLE_URL = "https://teletype.in/@mariamrouze/formula"
PREORDER_URL = "https://forms.gle/7AAixb78UeSALr4c9"  # замените на вашу ссылку на форму предзаписи

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # УСИЛЕННЫЙ ТЕКСТ ПРИВЕТСТВИЯ
    message_text = (
        "🔥 Привет! Я Мариам.\n\n"
        "Я бренд-менеджер и контент-маркетолог. За 4 года я прошла путь от нуля "
        "до 3 000 000 охвата в месяц и систематизировала всё в 5 простых формулах, "
        "которые работают в любой нише.\n\n"
        "📄 Вот моя статья — «Формула просмотров»:\n"
        f"{ARTICLE_URL}\n\n"
        "Внутри — информация, которую часто продают на платных курсах. "
        "Читай, сохраняй и сразу применяй.\n\n"
        "👇 А после прочтения жми на кнопку — я дам тебе задание, "
        "которое поможет внедрить формулы уже сегодня."
    )

    keyboard = [[InlineKeyboardButton("✅ Я прочитал(а) статью", callback_data="read_article")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message_text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "read_article":
        # Сообщение НЕ РЕДАКТИРУЕТСЯ — остаётся на месте.
        # Вместо этого отправляется НОВОЕ сообщение с заданием и формой.
        task_text = (
            "📝 Отлично! А теперь задание.\n\n"
            "Выбери одну из 5 формул из статьи и примени её к своему следующему ролику.\n"
            "Напиши в одном сообщении:\n"
            "1️⃣ Какую формулу ты выбрал(а)\n"
            "2️⃣ Как именно ты её применишь\n"
            "3️⃣ Какую тему возьмёшь для ролика\n\n"
            "💬 Пришли свой ответ сюда — я дам обратную связь.\n\n"
            "А если хочешь разобрать всё глубже и получить готовую систему под свой блог — "
            "оставь заявку на мини-курс «OH MY BRAND»:\n"
            f"{PREORDER_URL}\n\n"
            "Цена для тех, кто заполнит анкету сейчас — 5 500 ₽ (вместо 10 000 ₽). "
            "Анкета ни к чему не обязывает."
        )
        await query.message.reply_text(task_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — Начать и получить статью\n"
        "/help — Показать это сообщение"
    )


def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("Бот запущен и слушает сообщения...")
    application.run_polling()

if __name__ == "__main__":
    main()
