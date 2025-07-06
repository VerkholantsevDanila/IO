from flask import Flask, request
import mysql.connector
import os
import logging
import hashlib
import telebot
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Конфигурация базы данных
db_config = {
    'host': os.getenv("MYSQL_HOST", "mysql"),
    'user': os.getenv("MYSQL_USER", "root"),
    'password': os.getenv("MYSQL_PASSWORD", "RjhzdsqCkjy"),
    'database': os.getenv("MYSQL_DATABASE", "ioio"),
    'port': 3306
}

# Секрет и токен бота
YOOMONEY_SECRET = os.getenv("YOOMONEY_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)


@app.route('/yoomoney-webhook', methods=['POST'])
def yoomoney_webhook():
    data = request.form
    logging.info(f"[Webhook INCOMING] {data}")

    try:
        # Получаем все параметры из запроса
        notification_type = data.get('notification_type', '')
        operation_id = data.get('operation_id', '')
        amount = data.get('amount', '')
        withdraw_amount = data.get('withdraw_amount', '')
        currency_code = data.get('currency', '')  # цифровой код
        datetime_ = data.get('datetime', '')
        sender = data.get('sender', '')
        codepro = data.get('codepro', '')
        label = data.get('label', '')
        sha1_hash = data.get('sha1_hash', '')

        # Формируем строку для подписи
        hash_string = f"{notification_type}&{operation_id}&{amount}&{currency_code}&{datetime_}&{sender}&{codepro}&{YOOMONEY_SECRET}&{label}"
        calculated_hash = hashlib.sha1(hash_string.encode("utf-8")).hexdigest()

        if sha1_hash != calculated_hash:
            logging.warning("[Webhook] ❌ Hash mismatch — возможно фальшивка!")
            return "UNAUTHORIZED", 403

        # ✅ Подпись прошла — продолжаем
        # Преобразуем цифровой код валюты в строку
        currency = {
            '643': 'RUB',
            '840': 'USD',
            '978': 'EUR'
        }.get(currency_code, currency_code)

        # Преобразуем дату в datetime и в часовой пояс контейнера (например, Europe/Moscow)
        try:
            utc_time = datetime.strptime(datetime_, '%Y-%m-%dT%H:%M:%SZ')
            local_tz = pytz.timezone('Europe/Moscow')  # или другой timezone при необходимости
            datetime_obj = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
        except Exception:
            datetime_obj = datetime.now(pytz.timezone('Europe/Moscow'))  # fallback

        if label and withdraw_amount:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()

            # Обновляем баланс
            cursor.execute("UPDATE users SET balance = balance + %s WHERE tg_user_id = %s",
                           (int(float(withdraw_amount)), label))
            db.commit()

            # Запись в таблицу payments
            cursor.execute("""
                INSERT INTO payments (
                    tg_user_id, amount, withdraw_amount, currency, datetime,
                    operation_id, label, comment, type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'replenish')
            """, (
                int(label), float(amount), float(withdraw_amount), currency,
                datetime_obj, operation_id, label, sender
            ))
            db.commit()

            # Уведомляем пользователя
            cursor.execute("SELECT chat_id FROM users WHERE tg_user_id = %s", (label,))
            row = cursor.fetchone()
            cursor.close()
            db.close()

            if row:
                chat_id = row[0]
                bot.send_message(chat_id, f"🎉 Ваш баланс пополнен на {withdraw_amount} {currency}!")

            logging.info(f"[Webhook] ✅ Пополнение для tg_user_id={label} на {withdraw_amount} {currency} (поступило {amount})")

        return "OK"

    except Exception as e:
        logging.error(f"[Webhook ERROR] {e}")
        return "SERVER ERROR", 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8088)
