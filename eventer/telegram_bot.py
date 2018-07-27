# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from User import User
from UserRequest import UserRequest
from TelegramView import TelegramView

# Параметры для конфига системы
telegram_token = "524706088:AAGq3De-XCF-vb3-Z5NvScaoULoMAlosYO4"

# Создаем основные объекты для работы с телеграмом
updater = Updater(token=telegram_token)
dispatcher = updater.dispatcher

# Запуск сессии с базой данных
user_for_mysql = "eventer"
password_for_mysql = "Nhgbf86jmnIK"
engine = sqlalchemy.create_engine("mysql://" + user_for_mysql + ":" + password_for_mysql + "@localhost/eventer?charset=utf8", echo=False)
Session = sessionmaker(bind=engine)
session = Session()


def extract_telegram_user_id(update_from_telegram):
    """
    Extract telegram user id from Update
    :param update_from_telegram:
    :return: str or None
    """
    if update_from_telegram.effective_user:
        user_telegram_id = str(update_from_telegram.effective_user.id)
    else:
        user_telegram_id = None
    return user_telegram_id


# Initialize user
def get_user(update_from_telegram, session):
    user_telegram_id = extract_telegram_user_id(update_from_telegram)
    user = session.query(User).filter(User._telegram_id == user_telegram_id).first()
    if not user:
        user = User(telegram_id=user_telegram_id)
        session.add(user)
        session.commit()
        user = session.query(User).filter(User._telegram_id == user_telegram_id).first()
    return user


# Handler for first command - start
def start_command(bot, update):
    user = get_user(update, session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Привет, я помогу тебе выбрать мероприятие, на которое стоит сходить, '
                          'какого рода мероприятия тебя интересуют?')


# Handler for text message
def text_message(bot, update_from_telegram):
    user_message_text = update_from_telegram.message.text
    user = get_user(update_from_telegram, session)

    # Handle request
    user_request = UserRequest(user_message_text=user_message_text, session_with_db=session, user=user)
    data_for_answer = user_request.get_answer()
    text_answer = TelegramView.make_text_answer_from_data(data_for_answer)
    buttons_answer = TelegramView.get_buttons_for_message(data_for_answer)
    bot.send_message(chat_id=update_from_telegram.message.chat_id,
                     parse_mode='HTML',
                     text=text_answer,
                     reply_markup=buttons_answer)


# Создаем обработчики событий для телеграма
start_command_handler = CommandHandler('start', start_command)
text_message_handler = MessageHandler(Filters.text, text_message)
# Добавляем обработчики событий для телеграма в диспетчер
dispatcher.add_handler(start_command_handler)
dispatcher.add_handler(text_message_handler)
# Запускаем бесконечный цикл получения и обработки новых сообщений из телеграма
updater.start_polling(clean=True)
# Останавливаем бота, если были нажаты Ctrl + C
updater.idle()