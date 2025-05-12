import uuid
import yookassa
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

# Установка ключей для YooKassa
yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY

# Хранилище для payment_id (в памяти)
user_payments: dict[int, str] = {}

def create_payment(user_id: int) -> tuple[str, str]:
    """
    Создаёт платёж и возвращает ссылку на оплату и ID платежа.
    """
    payment_idempotence_key = str(uuid.uuid4())

    try:
        payment = yookassa.Payment.create({
            "amount": {
                "value": "50.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/m1major_bot"
            },
            "capture": True,
            "description": f"Оплата анкеты от пользователя {user_id}"
        }, payment_idempotence_key)
    except Exception as e:
        print(f"Ошибка при создании платежа: {e}")
        raise

    # Сохраняем ID платежа
    user_payments[user_id] = payment.id

    # Возвращаем ссылку и ID
    return payment.confirmation.confirmation_url, payment.id

def is_payment_successful(user_id: int) -> bool:
    """
    Проверяет, успешно ли прошла оплата.
    """
    payment_id = user_payments.get(user_id)
    if not payment_id:
        return False

    try:
        payment = yookassa.Payment.find_one(payment_id)
        return payment.status == "succeeded"
    except Exception as e:
        print(f"Ошибка при проверке статуса оплаты: {e}")
        return False
