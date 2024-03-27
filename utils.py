def calculate_profit(cashback, amount):
    """Рассчитывает выгоду"""
    try:
        cashback_value = float(cashback.replace("₽", "").replace(" ", "")) if cashback != 'N/A' else 0
        amount_value = float(amount.replace("₽", "").replace(" ", "")) if amount != 'N/A' else 0
        if cashback_value > 0.5 * amount_value:
            return cashback_value - amount_value
        else:
            return 0
    except ValueError:
        return 0