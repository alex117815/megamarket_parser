import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from parse import parse_products
from config import *

# Инициализация логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Список для хранения показанных товаров
shown_products = []

def start(update: Update, context: CallbackContext) -> None:
    """Отправляет инструкцию по команде /get_products"""
    update.message.reply_text('Введите /get_products для получения списка товаров')

def get_products(update: Update, context: CallbackContext) -> None:
    """Отправляет список товаров (по умолчанию 5 товаров)"""
    global shown_products
    products = parse_products()

    # Удаляем уже показанные товары из списка
    available_products = [p for p in products if p not in shown_products]

    # Берем первые 5 оставшихся товаров
    products_to_show = available_products[:5]

    if not products_to_show:
        update.message.reply_text('Все товары уже были показаны')
        return

    # Добавляем новые товары в список показанных
    shown_products.extend(products_to_show)

    for i, (name, amount, cashback, img, product_link, rating_count, rating_percentage, discont_elem, discont_text) in enumerate(products_to_show, start=1):
        if rating_percentage >= 80:
            stars = "⭐️⭐️⭐️⭐️⭐️"
        elif rating_percentage > 60 and rating_percentage < 80:
            stars = "⭐️⭐️⭐️⭐️"
        elif rating_percentage > 40 and rating_percentage <60:
            stars = "⭐️⭐️⭐️"
        
        if discont_text:
            amount = amount
        else:
            discont = "Без скидки"
            discont_text = amount
        product_info = f"▼Товар {i}▼:\n\n{name}\n\n╠Цена: <b>{amount}₽</b>\n╠Кешбек(сберспасибо): <b>{cashback}</b>⚡️\n\n╠Отзывов: {rating_count}👥\n╠Оценка: {stars}\n\n╠<a href='{product_link}'>Ссылка на товар</a>\n\n❤️СКИДКА\n╠{discont_elem}\n╠Цена без скидки:<b>{discont_text}</b>"
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=product_info, parse_mode='HTML')

def main() -> None:
    """Запуск бота"""
    updater = Updater(token)

    # Получаем диспетчер для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("get_products", get_products))

    # Запуск бота
    updater.start_polling()

    # Ожидание нажатия Ctrl+C для выхода
    updater.idle()

if __name__ == '__main__':
    main()