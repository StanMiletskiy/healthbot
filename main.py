from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import datetime
import pytz
import os

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_CHAT_ID = '94054314'  # Ваш Chat ID

OMST = pytz.timezone('Asia/Omsk')

# Глобальная переменная для хранения зарегистрированных чатов и их имен
registered_chats = {}


def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_name = update.message.chat.first_name  # Получаем имя пользователя

    if chat_id not in registered_chats:
        registered_chats[chat_id] = user_name
        print(f"Registered chat_id {chat_id} with name {user_name}"
              )  # Отладочное сообщение
    else:
        print(
            f"Chat_id {chat_id} is already registered")  # Отладочное сообщение

    update.message.reply_text(
        'Привет! Я буду спрашивать о твоем самочувствии каждый день в 11 утра по Омску.'
    )
    print(f"Current registered chats: {registered_chats}"
          )  # Отладочное сообщение


def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in registered_chats:
        del registered_chats[chat_id]
        print(f"Unregistered chat_id {chat_id}")  # Отладочное сообщение
        update.message.reply_text(
            'Вы отменили регистрацию и больше не будете получать уведомления о самочувствии.'
        )
    else:
        update.message.reply_text(
            'Вы не зарегистрированы для получения уведомлений.')
    print(f"Current registered chats after stop: {registered_chats}"
          )  # Отладочное сообщение


def ask_health(context: CallbackContext) -> None:
    job = context.job
    keyboard = [[InlineKeyboardButton("Отлично", callback_data='1')],
                [InlineKeyboardButton("Норм", callback_data='2')],
                [InlineKeyboardButton("Пойдет", callback_data='3')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=job.context,
                             text='Как самочувствие?',
                             reply_markup=reply_markup)
    print(f"Sent health check message to chat_id {job.context}"
          )  # Отладочное сообщение


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    chat_id = query.message.chat_id
    user_name = registered_chats.get(
        chat_id, 'Неизвестный пользователь')  # Получаем имя пользователя
    response = query.data

    response_text = {
        '1': 'Отлично',
        '2': 'Норм',
        '3': 'Пойдет'
    }.get(response, 'Неизвестно')

    query.edit_message_text(
        text=
        f"Ваш ответ: {response_text}\nСпасибо, встретимся завтра в 11 утра, отличного дня! ❤️"
    )

    # Уведомляем администратора
    context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"{user_name} ({chat_id}) ответил: {response_text}")


def main() -> None:
    updater = Updater(API_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Планирование ежедневного задания на 11:00 по Омскому времени для всех чатов
    def daily_job(context: CallbackContext) -> None:
        if not registered_chats:
            print("No chats registered for daily health check."
                  )  # Отладочное сообщение
            return  # Если нет зарегистрированных чатов, ничего не делаем
        print(f"Registered chats: {registered_chats}")  # Отладочное сообщение
        for chat_id in registered_chats:
            context.job_queue.run_once(ask_health, when=0, context=chat_id)
            print(f"Scheduled health check for chat_id {chat_id}"
                  )  # Отладочное сообщение

    j = updater.job_queue
    j.run_daily(daily_job, time=datetime.time(hour=11, minute=00, tzinfo=OMST))
    print("Daily job scheduled for 11:00 Omsk time.")  # Отладочное сообщение

    # Обработчик для команды /list_chats
    def list_chats(update: Update, context: CallbackContext) -> None:
        registered_chats_list = "\n".join([
            f"{chat_id}: {name}" for chat_id, name in registered_chats.items()
        ])
        update.message.reply_text(
            f"Registered chats:\n{registered_chats_list}")
        print(f"List of registered chats: {registered_chats}"
              )  # Отладочное сообщение

    dispatcher.add_handler(CommandHandler("list_chats", list_chats))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
