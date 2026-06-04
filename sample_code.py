"""Sample Python file used to test the AI code review pipeline."""


def calculate_discount(price, rate):
    discounted = price * rate
    return discounted


def divide(numerator, denominator):
    # TODO: handle zero
    result = numerator / denominator
    return result


def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query


def process_items(items):
    total = 0
    for i in range(len(items)):
        total = total + items[i]
    return total
