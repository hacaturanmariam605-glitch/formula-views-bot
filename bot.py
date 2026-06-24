import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Конфигурация ---
# Токен бота будет получен из переменной окружения, которую мы создадим на Railway
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TELEGRAM_TOKEN не установлена!")

# Ссылка на вашу статью в Notion
NOTION_URL = "https://app.notion.com/p/2d2b34d6f2f980428bc4f7ad4020699e"  # <--- ВСТАВЬТЕ СВОЮ ССЫЛКУ

# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветствие, ссылку на статью и кнопку для предзаписи."""
    # Текст сообщения
    message_text = (
        "Привет! 👋 Держи ссылку на мою статью «Формула просмотров».\n\n"
        "В ней я собрала весь свой практический опыт, который помог мне набрать "
        "1600+ подписчиков с нуля и начать сотрудничать с топ-брендами.\n\n"
        f"👉 {NOTION_URL}\n\n"
        "Прочитай статью, а потом я дам тебе небольшое задание."
    )
    # Кнопка для предзаписи
    keyboard = [[InlineKeyboardButton("📝 Хочу на предзапись курса", callback_data="preorder")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие на кнопку."""
    query = update.callback_query
    await query.answer()  # Отвечаем на нажатие, чтобы убрать "часики"
    if query.data == "preorder":
        await query.edit_message_text(
            "Отлично! 🎉 Скоро я запущу курс по созданию вирусного контента. "
            "Чтобы попасть на предзапись по специальной цене, оставьте свою заявку:\n\n"
            "[ССЫЛКА НА ФОРМУ ЗАЯВКИ]"  # <--- ВСТАВЬТЕ СВОЮ ССЫЛКУ НА ФОРМУ (Google Forms, Typeform и т.п.)
        )
    # Здесь можно добавить обработку других кнопок, если они появятся

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение с доступными командами."""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать и получить статью\n"
        "/help - Показать это сообщение"
    )

# --- Запуск бота ---
def main():
    # Создаём приложение
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # Регистрируем обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    print("Бот запущен и слушает сообщения...")
    application.run_polling()

if __name__ == "__main__":
    main()
