import requests
from bs4 import BeautifulSoup

url = "https://megamarket.ru/landing/obnovlyajsya/"

with requests.Session() as session:
    response = session.get(url)
    soup = BeautifulSoup(response.content, "lxml", from_encoding="utf-8")

    def parse_products():
        products = []
        product_items = soup.find_all("div", class_="product-list-item-link ddl_product ddl_product_link")

        for product in product_items:
            name = product.find("span", class_="product-list-item-title").text.strip()
            name = ''.join(c for c in name if c.isalnum() or c.isspace())

            amount_div = product.find("div", class_="amount")
            amount = amount_div.text.strip() if amount_div else "N/A"
            amount = amount.replace('₽', ' ' '').strip()
            

            dwcb = product.find("div", class_='money-bonus sm money-bonus_loyalty')
            cashback = dwcb.find("span", attrs={"data-test": 'bonus-amount'}).text if dwcb else "N/A"

            img = product.find("img", class_="lazy-img product-list-item-pic").get("src")

            product_link_elem = product.find("a", attrs={"data-test": "product-name-link"})
            product_link = f"https://megamarket.ru{product_link_elem.get('href')}" if product_link_elem else "Ссылка отсутствует"

            rating_count = product.find("div", class_="product-list-item-rating-count")
            rating_count = rating_count.text.strip() if rating_count else "Отзывы отсутствуют"

            rating_percentage = product.find("div", attrs={"data-test": "rating-stars-value"})
            rating_percentage = float(rating_percentage.get("style").split(":")[1][:-2]) if rating_percentage else 0

            discont_elem = product.find("div", attrs={"data-test": "discount-text"})
            discont_elem = discont_elem.text.strip() if discont_elem else 0
            discont_text = product.find("div", attrs={"data-test": "discount-price"})
            discont_text = discont_text.text.strip() if discont_text else 0


            products.append((name, amount, cashback, img, product_link, rating_count, rating_percentage, discont_elem, discont_text))
        return products