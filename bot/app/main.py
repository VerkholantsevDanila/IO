import os
import telebot
import mysql.connector
import qrcode
import time
import random
import string
import schedule
from threading import Thread
from io import BytesIO
from telebot import types
from datetime import datetime, timedelta

subscribe_server_url = os.getenv("SUBSCRIPTION_SERVER_URL")
subscriptions_max_count = int(os.getenv("SUBSCRIPTIONS_MAX_COUNT", 5)) # Maximum number of subscriptions per user
bot_token = os.getenv("BOT_TOKEN") # Telegram bot API key
db_config = {
    'host': os.getenv("MYSQL_HOST"),
    'user': os.getenv("MYSQL_USER"),
    'password': os.getenv("MYSQL_PASSWORD"),
    'database': os.getenv("MYSQL_DATABASE"),
    'port': int(os.getenv("MYSQL_PORT", 3306))
}
bot = telebot.TeleBot(bot_token)
db = mysql.connector.connect(**db_config)

@bot.message_handler(commands=['start'])
# Reaction on /start command
def user_check(message):
    # Check is user exists in database
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    sql = "SELECT * FROM users WHERE chat_id = %s"
    cursor = db.cursor()
    cursor.execute(sql, (chat_id,))
    user = cursor.fetchone()

    if user:
        # If user exists, update information about user in database
        sql = "UPDATE users SET chat_id = %s, username = %s, first_name = %s, last_name = %s WHERE tg_user_id = %s"
        val = (chat_id, username, first_name, last_name, user_id)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()

    else:
        # If user not exists, add information about user to database
        sql = "INSERT INTO users (chat_id, tg_user_id, username, first_name, last_name) VALUES (%s, %s, %s, %s, %s)"
        val = (chat_id, user_id, username, first_name, last_name)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()

    bot.delete_message(message.chat.id, message.message_id)
    with open('./start_banner.png', 'rb') as photo:
        bot.send_photo(chat_id, photo)
    bot.send_message(
        message.chat.id,
        "🔹<b>IO</b>🔹\n\n"
        "Добро пожаловать в наш VPN-сервис!\n\n"
        "🛡️ Защитите свою конфиденциальность\n"
        "🌍 Получите доступ к контенту без границ\n"
        "⚡ Высокая скорость, стабильность и анонимность\n\n"
        "<i>Для подключения выберите подписки в меню ниже</i> ⬇️",
        parse_mode='html'
    )

    menu(message)

@bot.message_handler(commands=['list'])
def list_subscriptions(message):
    new_subscription_list(message)

def menu(message):
    # Main menu page
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔘 Баланс', callback_data='balance'))
    markup.add(types.InlineKeyboardButton('🔘 Подписки', callback_data='subscriptions'))
    markup.add(types.InlineKeyboardButton('🔘 Помощь', callback_data='gethelp'))
    bot.send_message(message.chat.id,f'<b>Главное меню</b>', parse_mode='html', reply_markup=markup)
def gethelp(message):
    # Текст инструкции
    help_text = (
        "<b>📖 Инструкция по подключению:</b>\n\n"
        "1️⃣ Скачайте и установите приложение Hiddify (кнопки ниже).\n\n"
        "2️⃣ Подключите интересующую вас услугу через команду <b>/list</b>.\n\n"
        "3️⃣ После оплаты и покупки подписки, нажмите на активную подписку и выберите 'Показать QR-код' или 'Скопировать ссылку'.\n\n"
        "4️⃣ Запустите приложение, нажмите ➕ и добавьте через 'Добавить из буфера обмена' или отсканируйте QR-код."
    )

    # Отправка текста
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

    # Кнопки для загрузки приложений
    apps_markup = types.InlineKeyboardMarkup()
    apps_markup.add(
        types.InlineKeyboardButton("📱 Скачать для iOS", url="https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532"),
        types.InlineKeyboardButton("🤖 Скачать для Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com")
    )
    apps_markup.add(
        types.InlineKeyboardButton("🪟 Скачать для Windows", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.Msix"),
        types.InlineKeyboardButton("🍏 Скачать для macOS", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-MacOS.dmg")
    )
    apps_markup.add(
        types.InlineKeyboardButton("🐧 Скачать для Linux", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Linux-x64.AppImage")
    )
    apps_markup.add(
        types.InlineKeyboardButton("🅰️ Альтернатива для iOS (Streisand)", url="https://apps.apple.com/ru/app/streisand/id6450534064")
    )
    apps_markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))

    bot.send_message(message.chat.id, "👇 Выберите нужную платформу для установки Hiddify:", reply_markup=apps_markup)

#def gethelp(message):
    # Page with Instruction
#    markup = types.InlineKeyboardMarkup()
#    markup.add(types.InlineKeyboardButton('🔘 Инструкция EN', url='https://telegra.ph/IOIO-07-04-2'))
#    markup.add(types.InlineKeyboardButton('🔘 Инструкция RU', url='https://telegra.ph/IOIO-07-04-3'))
#    markup.add(types.InlineKeyboardButton('🏠Главное меню', callback_data='menu'))

#    help_text = (
#        "<b>📖 Инструкция по подключению:</b>\n\n"
#        "1️⃣ Скачайте и установите приложение Hiddify:\n"
#        "• <a href='https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532'>iOS</a>\n"
#        "• <a href='https://play.google.com/store/apps/details?id=app.hiddify.com'>Android</a>\n"
#        "• <a href='https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.Msix'>Windows</a>\n"
#        "• <a href='https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-MacOS.dmg'>macOS</a>\n"
#        "• <a href='https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Linux-x64.AppImage'>Linux</a>\n\n"
#        "Если не удаётся установить приложение из магазина — используйте альтернативу:\n"
#        "• <a href='https://apps.apple.com/ru/app/streisand/id6450534064'>iOS</a>\n\n"
#        "2️⃣ Подключите интересующую вас услугу через команду /list.\n\n"
#        "3️⃣ После оплаты и покупки подписки, нажмите на активную подписку и выберите показать QR-код или ссылку\n\n"
#        "4️⃣ Запустите приложение, нажмите ➕ и добавьте через 'Добавить из буфера обмена' или отсканируйте QR-код."
#    )

#    bot.send_message(message.chat.id, help_text, parse_mode='HTML', reply_markup=markup)

def balance(message):
    # Balance menu page
    markup = types.InlineKeyboardMarkup()

    # Подключение к БД (каждый раз новое!)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    cursor.execute("SELECT tg_user_id, balance FROM users WHERE chat_id = %s", (message.chat.id,))
    result = cursor.fetchone()
    cursor.close()
    db.close()  # Обязательно закрывай

    if result:
        tg_user_id, balance = result
        add_funds_url = f"https://yoomoney.ru/quickpay/shop-widget?writer=seller&targets=Paste%20your%20description%20here&targets-hint=&default-sum=150&label={tg_user_id}&button-text=12&payment-type-choice=on&hint=&successURL=&quickpay=shop&account=4100119221041643"
    else:
        tg_user_id = None
        balance = 0
        add_funds_url = "https://yoomoney.ru"

    markup.add(types.InlineKeyboardButton('➕ Пополнить баланс', url=add_funds_url))
    markup.add(types.InlineKeyboardButton('≡ История платежей', callback_data='pay_history'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))

    bot.send_message(
        message.chat.id,
        f"<b>Баланс: </b>{balance} RUB\n<b>Лимит подписок: </b>{subscriptions_max_count}",
        parse_mode='html',
        reply_markup=markup
    )



def pay_history(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='balance'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE chat_id = %s", (message.chat.id,))
    row = cursor.fetchone()

    if row:
        user_id = row[0]

        # Собираем объединённую историю из двух таблиц
        cursor.execute("""
            SELECT 'replenish' as type, withdraw_amount, currency, datetime, details
            FROM payments
            WHERE tg_user_id = %s

            UNION ALL

            SELECT 'subscription' as type, amount, currency, created_at, details
            FROM subscription_payments
            WHERE user_id = %s

            ORDER BY datetime DESC
            LIMIT 10
        """, (message.chat.id, user_id))

        rows = cursor.fetchall()
        if rows:
            history_text = "<b>📜 История платежей</b>\n\n"
            for p_type, amount, currency, dt, details in rows:
                dt_str = dt.strftime('%d.%m.%Y %H:%M')
                if p_type == 'replenish':
                    history_text += f"📥 <b>{amount:.2f} {currency}</b> — {dt_str}\n"
                elif p_type == 'subscription':
                    history_text += f"📤 <b>{amount:.2f} {currency}</b> — {dt_str}\n{details.strip()}\n\n"
        else:
            history_text = "<b>📜 История платежей</b>\n<i>❌ Платежи не найдены.</i>"
    else:
        history_text = "<b>📜 История платежей</b>\n<i>❌ Пользователь не найден.</i>"

    cursor.close()
    db.close()
    bot.send_message(message.chat.id, history_text, parse_mode='HTML', reply_markup=markup)



def subscriptions(message):
    # List all active user subscriptions
    bill_user_id = get_user_id(message)
    subscription = get_user_subscriptions(bill_user_id)
    active_subscriptions_count = int(len(subscription))
    markup = types.InlineKeyboardMarkup()
    for subscription in subscription:
        flag = get_flag_emoji(subscription[3])
        markup.add(types.InlineKeyboardButton(f"{flag} {subscription[2]} - ID {subscription[0]}", callback_data=f"subscription_{subscription[0]}"))
    if active_subscriptions_count < subscriptions_max_count:
        markup.add(types.InlineKeyboardButton('➕ Добавить подписку', callback_data='add_new_subscription'))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='menu'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_message(message.chat.id, f"<b>Активные подписки: </b>{active_subscriptions_count}", parse_mode='html', reply_markup=markup)

def subscription_info(message, subscription_id):
    # Menu page about selected active subscription
    markup = types.InlineKeyboardMarkup()
    subscription = get_subscription(subscription_id)
    name = subscription[0][2]
    flag = get_flag_emoji(subscription[0][3])
    region = subscription[0][3]
    active_until = datetime.fromtimestamp(subscription[0][4])
    token = subscription[0][1]
    cost = subscription[0][6]
    markup.add(types.InlineKeyboardButton('🔘 Показать ссылку', callback_data=f"subscriptionlink_{region}_{token}_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🔘 Показать QR код', callback_data=f"subscriptionqr_{region}_{token}_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🔻 Удалить подписку', callback_data=f"unsubscribe_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='subscriptions'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_message(message.chat.id, f"<b>ID Подписки: </b>{subscription_id}\n<b>Название: </b>{name}\n<b>Регион: </b>{flag} {region}\n<b>Цена: </b>{cost} RUB\n<b>Активна до: </b>{active_until}\n<b>Token: </b>{token}\n", parse_mode='html', reply_markup=markup)

def subscriptionlink_copy(message, region, token, subscription_id):
    # Copy Code menu page
    markup = types.InlineKeyboardMarkup()
    subscription_url = f"{subscribe_server_url}?token={token}"
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f"subscription_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_message(message.chat.id, f"Нажмите на ссылку подписки ниже, чтобы скопировать ее в буфер обмена::\n\n`{subscription_url}`", parse_mode="Markdown", reply_markup=markup)

def subscriptionqr_image(message, region, token, subscription_id):
    # QR Code menu page
    markup = types.InlineKeyboardMarkup()
    subscription_url = f"{subscribe_server_url}?token={token}"
    qr_img = generate_qr_code(subscription_url)  # Generate QR code
    byte_io = BytesIO()  # Save QR code to BytesIO
    qr_img.save(byte_io, 'PNG')
    byte_io.seek(0)  # Move cursor to zero point
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f"subscription_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_photo(message.chat.id, byte_io, reply_markup=markup)

def new_subscription_list(message):
    # List all available subscriptions to purchase menu page
    all_subscriptions = get_all_subscriptions()
    markup = types.InlineKeyboardMarkup()
    for subscription in all_subscriptions:
        subscription_id = subscription[0]
        subscription_name = subscription[1]
        flag = get_flag_emoji(subscription[3])
        cost = subscription[4]
        markup.add(types.InlineKeyboardButton(f"{flag} {subscription_name} - {cost} RUB", callback_data=f"new_subscription_info_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='menu'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_message(message.chat.id, '<b>Активные подписки</b>', parse_mode='html', reply_markup=markup)

def new_subscription_info(message, subscription_id):
    # Purchase subscription (info about new subscription) menu page
    subscription = get_new_subscription_info(subscription_id)
    name = subscription[0][1]
    period_seconds = int(subscription[0][2])
    flag = get_flag_emoji(subscription[0][3])
    cost = subscription[0][4]
    current_time = int(time.time())
    active_until = datetime.fromtimestamp(current_time + period_seconds)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Купить подписку', callback_data=f"purchase_subscription_{subscription_id}_{period_seconds}"))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='add_new_subscription'))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_message(message.chat.id, f"<b>Подписка: </b>{flag} {name}\n<b>Активна до: </b>{active_until}\n<b>Цена: </b>{cost} RUB\n<i>Обратите внимание, что у вас должно быть не более {subscriptions_max_count} активных подписок!</i>\n<i>После достижения указанного лимита вы не сможете подключить дополнительные подписки.</i>\n", parse_mode='html', reply_markup=markup)

def unsubscribe(message, subscription_id):
    # Unsubscribe menu page
    markup = types.InlineKeyboardMarkup()
    subscription = get_subscription(subscription_id)
    name = subscription[0][2]
    flag = get_flag_emoji(subscription[0][3])
    region = subscription[0][3]
    active_until = datetime.fromtimestamp(subscription[0][4])
    token = subscription[0][1]
    cost = subscription[0][6]
    markup.add(types.InlineKeyboardButton('🔻 Да, удалить подписку', callback_data=f"remove_subscription_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f"subscription_{subscription_id}"))
    markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))
    bot.send_message(message.chat.id, f"<b>Вы уверены, что хотите удалить подписку??</b>\n<b>ID Подписки: </b>{subscription_id}\n<b>Название: </b>{name}\n<b>Регион: </b>{flag} {region}\n<b>Цена: </b>{cost} RUB\n<b>Активна до: </b>{active_until}\n<b>Токен: </b>{token}\n<b>Обратите внимание, что это действие нельзя отменить.!</b>", parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'balance':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        balance(callback.message)
    elif callback.data == 'menu':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        menu(callback.message)
    elif callback.data == 'gethelp':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        gethelp(callback.message)
    elif callback.data == 'pay_history':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        pay_history(callback.message)
    elif callback.data == 'subscriptions':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscriptions(callback.message)
    elif callback.data.startswith("subscription_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        subscription_id = subscription_data[1]
        subscription_info(callback.message, subscription_id)
    elif callback.data.startswith("subscriptionlink_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        region = subscription_data[1]
        token = subscription_data[2]
        subscription_id = subscription_data[3]
        subscriptionlink_copy(callback.message, region, token, subscription_id)
    elif callback.data.startswith("subscriptionqr_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        region = subscription_data[1]
        token = subscription_data[2]
        subscription_id = subscription_data[3]
        subscriptionqr_image(callback.message, region, token, subscription_id)
    elif callback.data == 'add_new_subscription':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        new_subscription_list(callback.message)
    elif callback.data.startswith("new_subscription_info_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        subscription_id = subscription_data[3]
        new_subscription_info(callback.message, subscription_id)
    elif callback.data.startswith("purchase_subscription_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        subscription_id = subscription_data[2]
        period = subscription_data[3]
        purchase_subscription(callback.message, subscription_id, period)
    elif callback.data.startswith("unsubscribe_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        subscription_id = subscription_data[1]
        unsubscribe(callback.message, subscription_id)
    elif callback.data.startswith("remove_subscription_"):
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        subscription_data = callback.data.split("_")
        subscription_id = subscription_data[2]
        remove_subscription(callback.message, subscription_id)

def get_user_id(message):
    # Get billing user ID from database
    chat_id = message.chat.id
    sql = 'SELECT id FROM users WHERE chat_id = %s'
    val = (chat_id,)
    cursor = db.cursor()
    cursor.execute(sql, val)
    result = cursor.fetchall()
    cursor.close()
    billing_user_id = result[0][0]
    return billing_user_id

def get_user_subscriptions(bill_user_id):
    # Get all user subscriptions from billing
    sql = 'SELECT tok.id, tok.token, tar.name, tar.region, tok.end_date, tok.is_active FROM tokens tok JOIN tariffs tar ON tok.tariff_id = tar.id WHERE user_id = %s'
    val = (bill_user_id,)
    cursor = db.cursor()
    cursor.execute(sql, val)
    result = cursor.fetchall()
    cursor.close()
    subscription = result
    return subscription

def get_subscription(subscription_id):
    # Get information about subscription from billing
    sql = 'SELECT tok.id, tok.token, tar.name, tar.region, tok.end_date, tok.is_active, tar.cost FROM tokens tok JOIN tariffs tar ON tok.tariff_id = tar.id WHERE tok.id = %s'
    val = (subscription_id,)
    cursor = db.cursor()
    cursor.execute(sql, val)
    result = cursor.fetchall()
    cursor.close()
    return result

def get_all_subscriptions():
    # Get all available subscriptions from billing (all tariffs)
    sql = 'SELECT id, name, period, region, cost FROM tariffs'
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    return result

def get_new_subscription_info(subscription_id):
    # Get new subscription info from billing (tariff info)
    sql = 'SELECT id, name, period, region, cost FROM tariffs WHERE id = %s'
    val = (subscription_id,)
    cursor = db.cursor()
    cursor.execute(sql, val)
    result = cursor.fetchall()
    cursor.close()
    return result

def purchase_subscription(message, subscription_id, period):
    user_id = get_user_id(message)
    cursor = db.cursor()

    # Получаем цену подписки
    cursor.execute("SELECT cost FROM tariffs WHERE id = %s", (subscription_id,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        bot.send_message(message.chat.id, "❌ Подписка не найдена.")
        return
    cost = int(result[0])

    # СВЕЖИЙ запрос баланса из базы, прямо перед списанием
    cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")
        return
    balance = int(result[0])

    # Проверяем баланс — уже актуальный

    if balance < cost:
        # Сформируем URL на пополнение
        add_funds_url = f"https://yoomoney.ru/quickpay/shop-widget?writer=seller&targets=VPN&default-sum={cost}&label={message.chat.id}&button-text=12&payment-type-choice=on&quickpay=shop&account=4100119221041643"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('➕ Пополнить баланс', url=add_funds_url))
        markup.add(types.InlineKeyboardButton('≡ История платежей', callback_data='pay_history'))
        markup.add(types.InlineKeyboardButton('🏠 Главное меню', callback_data='menu'))

        bot.send_message(
            message.chat.id,
            f"<b>❌ Недостаточно средств</b>\n\n"
            f"💰 Баланс: <b>{balance} руб.</b>\n"
            f"💳 Необходимо оплатить: <b>{cost} руб.</b>",
            parse_mode='html',
            reply_markup=markup
        )
        cursor.close()
        return

#    if balance < cost:
#        cursor.close()
#        bot.send_message(message.chat.id, f"❌ Не достаточно средств. Ваш баланс: {balance} RUB, required: {cost} RUB")
#        menu(message)
#        return

    # Списываем деньги и создаем подписку
    new_balance = balance - cost
    cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))

    token = generate_token()
    start_date = int(time.time())
    period_seconds = int(period)
    end_date = start_date + period_seconds
    # Добавляем запись в таблицу tokens с активными подписками
    cursor.execute(
        "INSERT INTO tokens(user_id, tariff_id, token, start_date, end_date) VALUES(%s, %s, %s, %s, %s)",
        (user_id, subscription_id, token, start_date, end_date)
    )

    token_id = cursor.lastrowid  # Сохраняем ID токена сразу после вставки
 

    # Получаем название и цену подписки
    cursor.execute("SELECT name FROM tariffs WHERE id = %s", (subscription_id,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        bot.send_message(message.chat.id, "❌ Подписка не найдена.")
        return
    subscription_name = result[0]

    cursor.execute(
      "INSERT INTO subscription_payments (tg_user_id, user_id, tariff_id, token_id, amount, currency, details) VALUES (%s, %s, %s, %s, %s, %s, %s)",
      (
        message.chat.id,
        user_id,
        subscription_id,
        token_id,
        cost,
        'RUB',
        f"🔐 Подписка: {subscription_name} | Остаток: {new_balance} RUB"
      )
    )

    db.commit()
    cursor.close()
    bot.send_message(message.chat.id, f"✅ Подписка оплачена! {cost} RUB списана со счета.")
    subscriptions(message)


def remove_subscription(message, subscription_id):
    # Remove user subscription
    sql = 'DELETE FROM tokens WHERE id = %s'
    val = (subscription_id,)
    cursor = db.cursor()
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    subscriptions(message)

def get_flag_emoji(country_code):
    # Get flag emoji from region code
    country_code = country_code.upper()
    if len(country_code) != 2 or not country_code.isalpha():
        raise ValueError("Country code must be two letters (e.g., 'ru', 'us', 'fi')")
    flag_emoji = "".join(chr(ord(char) + 127397) for char in country_code)
    return flag_emoji

def generate_token(length=24):
    # Generate token
    characters = string.ascii_letters + string.digits
    token = ''.join(random.choice(characters) for _ in range(length))
    return token

def generate_qr_code(subscription_url):
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(subscription_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

################################################################
def expired_subscription_del():
    current_time = int(time.time())
    sql = "DELETE FROM tokens WHERE end_date < %s"
    cursor = db.cursor()
    cursor.execute(sql, (current_time,))
    db.commit()
    cursor.close()

def run_scheduler():
    schedule.every(5).minutes.do(expired_subscription_del)
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()
################################################################

bot.polling(none_stop=True)
