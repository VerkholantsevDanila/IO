from flask import Flask, request
import mysql.connector
import os
import logging
import hashlib
import telebot
from dotenv import load_dotenv

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
        # Основные параметры уведомления
        notification_type = data.get('notification_type', '')
        operation_id = data.get('operation_id', '')
        amount = data.get('amount', '')  # сумма, поступившая на счёт продавца (уже после комиссии)
        withdraw_amount = data.get('withdraw_amount', '')  # сумма, которую отправил пользователь
        currency = data.get('currency', '')
        datetime_ = data.get('datetime', '')
        sender = data.get('sender', '')
        codepro = data.get('codepro', '')
        label = data.get('label', '')
        sha1_hash = data.get('sha1_hash', '')

        # Проверка подписи
        hash_string = f"{notification_type}&{operation_id}&{amount}&{currency}&{datetime_}&{sender}&{codepro}&{YOOMONEY_SECRET}&{label}"
        calculated_hash = hashlib.sha1(hash_string.encode("utf-8")).hexdigest()

        if sha1_hash != calculated_hash:
            logging.warning("[Webhook] ❌ Hash mismatch — возможно фальшивка!")
            return "UNAUTHORIZED", 403

        # Обработка пополнения
        if label and withdraw_amount:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()

            # Обновляем баланс по фактически отправленной пользователем сумме (без вычета комиссии)
            sql = "UPDATE users SET balance = balance + %s WHERE tg_user_id = %s"
            val = (int(float(withdraw_amount)), label)
            cursor.execute(sql, val)
            db.commit()

            # Получаем chat_id пользователя
            cursor.execute("SELECT chat_id FROM users WHERE tg_user_id = %s", (label,))
            row = cursor.fetchone()
            cursor.close()
            db.close()

            if row:
                chat_id = row[0]
                bot.send_message(chat_id, f"🎉 Ваш баланс пополнен на {withdraw_amount} RUB!")

            # В лог — amount (что дошло до продавца), но текстово показываем обе суммы
            logging.info(f"[Webhook] ✅ Пополнение для tg_user_id={label} на {withdraw_amount} RUB (на счёт поступило {amount} RUB)")

        return "OK"

    except Exception as e:
        logging.error(f"[Webhook ERROR] {e}")
        return "SERVER ERROR", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8088)
