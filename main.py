import logging
import math
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from functools import lru_cache

from parse import parse_products
from utils import calculate_profit
from config import token

# Инициализация логирования
logging.basicConfig(level=logging.INFO, filename='bot.log', format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота и диспетчера
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Состояния для диалога выбора URL, количества товаров и критерия сортировки
class Form(StatesGroup):
    URL_CHOICE = State()
    PRODUCT_COUNT = State()
    SORT_CHOICE = State()

liked_products = []

@lru_cache(maxsize=128)
def get_products(url):
    return parse_products(url)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="1. Обновляйся"), types.KeyboardButton(text="2. Мега выгода"), types.KeyboardButton(text="3. Главная страница"))
    await message.answer("Выберите интересующий вас URL:", reply_markup=keyboard)
    await Form.URL_CHOICE.set()  # Переходим к выбору URL

# Обработчик выбора URL
@dp.message_handler(state=Form.URL_CHOICE)
async def url_choice(message: types.Message, state: FSMContext):
    url_choice = message.text

    url = ""
    if url_choice == '1. Обновляйся':
        url = "https://megamarket.ru/landing/obnovlyajsya/"
    elif url_choice == '2. Мега выгода':
        url = "https://megamarket.ru/landing/megavygoda/"
    elif url_choice == '3. Главная страница':
        url = "https://megamarket.ru/"

    # Сохраняем выбранный URL
    await state.update_data(url=url)
    logging.info(f"Выбран URL: {url}")

    await message.answer(f"Вы выбрали URL: {url}. Теперь введите количество товаров, которое хотите получить (например, 5).", reply_markup=types.ReplyKeyboardRemove())
    await Form.PRODUCT_COUNT.set()  # Переходим к вводу количества товаров

# Обработчик ввода количества товаров
@dp.message_handler(state=Form.PRODUCT_COUNT)
async def product_count(message: types.Message, state: FSMContext):
    try:
        product_count = int(message.text)
        await state.update_data(product_count=product_count)
        await message.answer("Спасибо! Теперь выберите критерий сортировки:", reply_markup=sort_keyboard())
        await Form.SORT_CHOICE.set()  # Переход к состоянию выбора сортировки
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

# Функция для создания клавиатуры с критериями сортировки
def sort_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton(text="По кешбэку"), types.KeyboardButton(text="По скидке"), types.KeyboardButton(text="По личной выгоде"))
    return keyboard

# Обработчик выбора критерия сортировки
@dp.message_handler(state=Form.SORT_CHOICE)
async def sort_choice(message: types.Message, state: FSMContext):
    choice = message.text.lower()
    data = await state.get_data()
    url = data.get('url')
    product_count = data.get('product_count', 5)

    if url:
        try:
            products = get_products(url)
        except Exception as e:
            logging.error(f"Ошибка при парсинге сайта: {str(e)}")
            await message.answer(f"Ошибка при парсинге сайта: {str(e)}")
            return

        # Фильтруем товары с недоступными значениями кешбэка и стоимости
        available_products = [product for product in products if product[1] != 'N/A' and product[2] != 'N/A']

        # Сортируем товары по выбранному критерию
        sorted_products = sort_products(choice, available_products)

        total_products = len(sorted_products)
        pages = math.ceil(total_products / product_count)

        await show_products(message, sorted_products, product_count, pages, state)

        await state.reset_state()

    else:
        await message.answer_text("Пожалуйста, сначала выберите URL с помощью команды /start")

# Функция для сортировки товаров по выбранному критерию
def sort_products(choice, available_products):
    if choice == 'по кешбэку':
        sorted_products = sorted(available_products, key=lambda x: float(x[2].replace("₽", "").replace(" ", "")) if x[2] != 'N/A' else 0, reverse=True)
    elif choice == 'по скидке':
        sorted_products = sorted(available_products, key=lambda x: (float(x[7].replace("₽", "").replace(" ", "")) if x[7] != 'N/A' and x[7].isdigit() else float('-inf'), x[7] == 'N/A'), reverse=True)
    elif choice == 'по личной выгоде':
        sorted_products = sorted(available_products, key=lambda x: calculate_profit(x[2], x[1]), reverse=True)
    else:
        sorted_products = available_products

    return sorted_products

# Функция для отображения товаров пользователю
async def show_products(message, sorted_products, product_count, pages, state):
    page = 1
    per_page = product_count

    while True:
        start = (page - 1) * per_page
        end = start + per_page
        products_to_show = sorted_products[start:end]

        for i, product in enumerate(products_to_show, start=start+1):
            await send_product_info(message, product, i)

        if page == pages:
            ask_again = await message.answer("Нужно ли вывести товары еще раз? (да/нет)")
            response = await dp.wait_for(lambda msg: msg.text.lower() in ['да', 'нет'], timeout=60)
            if response.text.lower() == 'да':
                page = 1
                continue
            else:
                break

        page += 1
        if page <= pages:
            if pages > 1:
                page_info = f"Страница {page}/{pages}."
            else:
                page_info = "Всего товаров: {total_products}"

            await message.answer(f"{page_info} Нажмите /next для следующей страницы или /stop для завершения.")
            response = await dp.wait_for(lambda msg: msg.text.lower() in ['/stop', '/next'], timeout=10)
            if response.text == '/stop':
                break
            elif response.text == '/next':
                if page == pages:
                    await message.answer("Вы уже находитесь на последней странице.")
                else:
                    continue
        else:
            break

# Функция для отправки информации о товаре
async def send_product_info(message, product, index):
    name, amount, cashback, img, product_link, rating_count, rating_percentage, discont_elem, discont_text = product
    stars = "⭐️" * int(rating_percentage / 18)

    # Рассчитываем скидку
    discount, discount_message = calculate_discount(amount, discont_text)

    # Рассчитываем чистые траты
    net_expenses, net_expenses_message = calculate_net_expenses(amount, cashback)

    # Формируем информацию о товаре
    product_info = f"▼Товар {index}▼:\n\n{name}\n\n╠Цена: <b>{amount}</b>\n╠Кешбек(сберспасибо): <b>{cashback}</b>⚡️\n\n╠<b>{net_expenses_message}</b>\n╠Отзывов: {rating_count}👥\n╠Оценка: {stars}\n\n╠<a href='{product_link}'>Ссылка на товар</a>\n\n{discount_message}\n\n/like_{index} - Добавить в избранное"
    await message.answer_photo(photo=img, caption=product_info, parse_mode='HTML')

# Функция для рассчета скидки
def calculate_discount(amount, discont_text):
    if discont_text and amount and discont_text != 'N/A' and amount != 'N/A':
        try:
            discount = float(discont_text.replace("₽", "").replace(" ", "")) - float(amount.replace("₽", "").replace(" ", ""))
            discount_message = f"❤️СКИДКА: {discount}₽\n╠Цена без скидки: {discont_text}"
        except ValueError:
            discount = 0
            discount_message = "❤️СКИДКА: Без скидки"
    else:
        discount = 0
        discount_message = "❤️СКИДКА: Без скидки"

    return discount, discount_message

# Функция для рассчета чистых трат
def calculate_net_expenses(amount, cashback):
    try:
        net_expenses = float(amount.replace("₽", "").replace(" ", "")) - float(cashback.replace("₽", "").replace(" ", ""))
        net_expenses_message = f"Чистые траты: {net_expenses}₽"
    except ValueError:
        net_expenses_message = ""

    return net_expenses, net_expenses_message

# Обработчик команды /like_
@dp.message_handler(lambda message: message.text.startswith('/like_'))
async def like_product(message: types.Message, state: FSMContext):
    product_index = int(message.text.split('_')[1]) - 1
    data = await state.get_data()
    url = data.get('url')
    products = get_products(url)
    if 0 <= product_index < len(products):
        liked_product = products[product_index]
        liked_products.append(liked_product)
        await message.answer(f"Товар '{liked_product[0]}' добавлен в избранное.")

        # Получаем общее количество товаров и количество страниц
        product_count = data.get('product_count', 5)
        total_products = len(products)
        pages = math.ceil(total_products / product_count)

        # Выводим информацию о количестве оставшихся страниц или товаров
        if pages > 1:
            remaining_pages = pages - (product_index // product_count) - 1
            if remaining_pages > 0:
                await message.answer(f"Осталось {remaining_pages} страниц товаров.")
            else:
                await message.answer("Все товары просмотрены.")
        else:
            remaining_products = total_products - (product_index + 1)
            await message.answer(f"Осталось {remaining_products} товаров.")
    else:
        await message.answer("Некорректный номер товара.")

# Обработчик команды /liked
@dp.message_handler(commands=['liked'])
async def show_liked(message: types.Message):
    if not liked_products:
        await message.answer("Вы еще не добавили товары в избранное.")
    else:
        for i, product in enumerate(liked_products, start=1):
            await send_product_info(message, product, i)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)