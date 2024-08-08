from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Список каналов и текста рекламного сообщения по умолчанию
DEFAULT_CHANNELS = ['CHANNEL_ID_1', 'CHANNEL_ID_2']
DEFAULT_ADVERTISEMENT = "Здесь ваше рекламное сообщение!"

# Статистика рассылки
total_messages_sent = 0
successful_deliveries = 0

# Цена за рекламную рассылку (в копейках)
PRICE_PER_ADVERTISEMENT = 1000

# Словарь для хранения предпочтений языка пользователей
user_language_preferences = {}


# Функция отправки рекламного сообщения в каналы
def send_advertisement(context):
    global total_messages_sent, successful_deliveries
    for channel_id in context.job.context['channels']:
        try:
            context.bot.send_message(chat_id=channel_id, text=context.job.context['advertisement'])
            logger.info(f"Реклама отправлена в канал {channel_id}")
            successful_deliveries += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке рекламы в канал {channel_id}: {e}")
        finally:
            total_messages_sent += 1


# Обработчик команды /advertise
def advertise(update, context):
    # Проверяем, заданы ли параметры рекламы и каналов
    if 'advertisement' in context.args and 'channels' in context.args:
        advertisement = ' '.join(context.args[0:])
        channels = context.args[1:]
    else:
        advertisement = DEFAULT_ADVERTISEMENT
        channels = DEFAULT_CHANNELS

    # Проверяем, хватает ли пользователю средств для оплаты
    user_balance = get_user_balance(update.effective_user.id)
    if user_balance >= PRICE_PER_ADVERTISEMENT:
        # Отправляем рекламу в указанные каналы
        job_context = {'channels': channels, 'advertisement': advertisement}
        context.job_queue.run_once(send_advertisement, 0, context=job_context)
        # Вычитаем стоимость рекламы из баланса пользователя
        update_user_balance(update.effective_user.id, -PRICE_PER_ADVERTISEMENT)
        update.message.reply_text(
            f"Реклама разослана в выбранные каналы. С вашего счета списано {PRICE_PER_ADVERTISEMENT / 100} руб.",
            reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("У вас недостаточно средств на счете. Пополните баланс.",
                                  reply_markup=ReplyKeyboardRemove())


# Обработчик команды /language
def set_language(update, context):
    reply_keyboard = [['English', 'Русский']]
    update.message.reply_text(
        "Выберите язык интерфейса:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


# Обработчик выбора языка пользователем
def select_language(update, context):
    text = update.message.text
    user_language_preferences[update.effective_user.id] = text.lower()
    update.message.reply_text(f"Язык интерфейса установлен на {text}.")


# Функция отправки статистики рассылки
def show_stats(update, context):
    update.message.reply_text(
        f"Всего сообщений отправлено: {total_messages_sent}\nУспешно доставлено: {successful_deliveries}")


def main():
    # Токен вашего бота
    token = '6345957511:AAFIo_NBRL_s3iwRAJ-WQ65SD-1rXH_ZLE8'
    # Создаем объект updater и передаем ему токен бота
    updater = Updater(token, use_context=True)
    # Получаем объект диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher
    # Регистрируем обработчик команды /advertise
    dispatcher.add_handler(CommandHandler('advertise', advertise))
    # Регистрируем обработчик команды /language
    dispatcher.add_handler(CommandHandler('language', set_language))
    # Регистрируем обработчик для выбора языка
    dispatcher.add_handler(MessageHandler(Filters.regex('^(English|Русский)$'), select_language))
    # Регистрируем команду для отображения статистики рассылки
    dispatcher.add_handler(CommandHandler('stats', show_stats))

    # Запускаем бота
    updater.start_polling()

    # Запускаем планировщик
    scheduler = BackgroundScheduler()
    scheduler.start()

    updater.idle()


if __name__ == '__main__':
    main()
