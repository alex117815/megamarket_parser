import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def parse_products(url):
    """
    Парсит информацию о продуктах с веб-страницы и возвращает список кортежей с информацией о продуктах.
    
    :param url: URL-адрес веб-страницы с продуктами
    :return: список кортежей с информацией о продуктах
    """
    products = []
    try:
        with requests.Session() as session:
            response = session.get(url)
            soup = BeautifulSoup(response.content, "lxml", from_encoding="utf-8")

            product_items = soup.find_all("div", class_="product-list-item-link ddl_product ddl_product_link")

            for product in product_items:
                name_elem = product.find("span", class_="product-list-item-title")
                name = ''.join(c for c in name_elem.text.strip() if c.isalnum() or c.isspace()) if name_elem else "N/A"

                amount_elem = product.find("div", class_="amount")
                amount = amount_elem.text.strip().replace('₽', '').strip() if amount_elem else "N/A"

                cashback_elem = product.find("div", class_='money-bonus sm money-bonus_loyalty')
                cashback = cashback_elem.find("span", attrs={"data-test": 'bonus-amount'}).text.strip() if cashback_elem else "N/A"

                img = product.find("img", class_="lazy-img product-list-item-pic").get("src")

                product_link_elem = product.find("a", attrs={"data-test": "product-name-link"})
                product_link = urljoin(url, product_link_elem.get('href')) if product_link_elem else "Ссылка отсутствует"

                rating_count_elem = product.find("div", class_="product-list-item-rating-count")
                rating_count = rating_count_elem.text.strip() if rating_count_elem else "Отзывы отсутствуют"

                rating_percentage_elem = product.find("div", attrs={"data-test": "rating-stars-value"})
                rating_percentage = float(rating_percentage_elem.get("style").split(":")[1][:-2]) if rating_percentage_elem else 0

                discont_elem = product.find("div", attrs={"data-test": "discount-text"})
                discont = discont_elem.text.strip() if discont_elem else "Без скидки"

                discont_text_elem = product.find("div", attrs={"data-test": "discount-price"})
                discont_text = discont_text_elem.text.strip() if discont_text_elem else "N/A"

                products.append((name, amount, cashback, img, product_link, rating_count, rating_percentage, discont, discont_text))
    except Exception as e:
        print(f"Ошибка при получении или обработке товаров: {e}")
    return products
