from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler
import datetime
import random
from database import (get_user_balance, update_user_balance, get_last_claim, 
                      update_last_claim, log_user_login, get_total_users, 
                      get_total_logins, is_admin)
import config

# Состояния для ConversationHandler
WAITING_FOR_BET = 0

# Словарь для хранения временных данных
user_states = {}

# Создаем клавиатуру один раз
DEFAULT_KEYBOARD = ReplyKeyboardMarkup([['Играть', 'Баланс'], ['Ежедневная награда']], resize_keyboard=True)

# Клавиатура для администраторов
ADMIN_KEYBOARD = ReplyKeyboardMarkup([
    ['Играть', 'Баланс'], 
    ['Ежедневная награда'], 
    ['Статистика бота']
], resize_keyboard=True)

# Функция для выбора клавиатуры в зависимости от прав пользователя
def get_keyboard(user_id):
    return ADMIN_KEYBOARD if user_id in config.ADMIN_IDS else DEFAULT_KEYBOARD

# Функция для команды /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    log_user_login(user_id)
    
    await update.message.reply_text(
        'Добро пожаловать в Казино Бот! Выберите действие:',
        reply_markup=get_keyboard(user_id)
    )


# Функция для начала игры в слоты
async def slots_start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    await update.message.reply_text(
        'Введите сумму ставки (От 10-1000):', 
        reply_markup=get_keyboard(user_id)
    )
    return WAITING_FOR_BET


# Функция для обработки ставки
async def process_bet(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    try:
        bet_amount = int(update.message.text)
        if bet_amount < 10 or bet_amount > 1000:
            await update.message.reply_text(
                'Ставка должна быть от 10 до 1000 тугриков.', 
                reply_markup=get_keyboard(user_id)
            )
            return WAITING_FOR_BET

        balance = get_user_balance(user_id)
        if balance < bet_amount:
            await update.message.reply_text(
                f'Недостаточно тугриков для игры. Ваш баланс: {balance} тугриков.',
                reply_markup=get_keyboard(user_id)
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f'Ваша ставка: {bet_amount}', 
            reply_markup=get_keyboard(user_id)
        )

        # Игровая логика
        balance -= bet_amount
        symbols = ['', '', '', '', '']
        result = [random.choice(symbols) for _ in range(3)]

        if result[0] == result[1] == result[2]:
            win_amount = bet_amount * 5
            balance += win_amount
            message = f'Поздравляем! Вы выиграли {win_amount} тугриков!\nСтавка: {bet_amount}\nРезультат: {" ".join(result)}'
        else:
            message = f'Вы проиграли {bet_amount} тугриков.\nРезультат: {" ".join(result)}'

        update_user_balance(user_id, balance)
        await update.message.reply_text(
            message, 
            reply_markup=get_keyboard(user_id)
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            'Пожалуйста, введите целое число.', 
            reply_markup=get_keyboard(user_id)
        )
        return WAITING_FOR_BET


# Функция для отмены разговора
async def cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    await update.message.reply_text(
        'Игра отменена.', 
        reply_markup=get_keyboard(user_id)
    )
    return ConversationHandler.END


# Функция для команды /balance
async def balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(
        f'Ваш баланс: {balance} тугриков.', 
        reply_markup=get_keyboard(user_id)
    )


# Функция для команды /daily
async def daily(update: Update, context: CallbackContext) -> None:
    try:
        user_id = update.message.from_user.id
        last_claim = get_last_claim(user_id)
        now = datetime.datetime.now()

        if last_claim is None:
            # Первое получение награды
            balance = get_user_balance(user_id) + 80
            update_user_balance(user_id, balance)
            update_last_claim(user_id)
            await update.message.reply_text(
                'Вы получили 80 тугриков! Следующий подарок можно получить через 12 часов.',
                reply_markup=get_keyboard(user_id)
            )
            return

        # Проверяем, прошли ли 12 часов
        time_diff = now - last_claim
        seconds_passed = time_diff.total_seconds()
        seconds_left = 12 * 3600 - seconds_passed
        
        if seconds_left > 0:
            hours_passed = int(seconds_passed // 3600)
            minutes_passed = int((seconds_passed % 3600) // 60)
            seconds_passed_remainder = int(seconds_passed % 60)
            hours_left = int(seconds_left // 3600)
            minutes_left = int((seconds_left % 3600) // 60)
            seconds_left_remainder = int(seconds_left % 60)

            passed_str = f"{hours_passed} ч. {minutes_passed} мин. {seconds_passed_remainder} сек."
            left_str = f"{hours_left} ч. {minutes_left} мин. {seconds_left_remainder} сек."

            await update.message.reply_text(
                f'Прошло всего {passed_str}!\nПриходи через {left_str}.',
                reply_markup=get_keyboard(user_id)
            )
            return

        # Выдаем награду
        balance = get_user_balance(user_id) + 80
        update_user_balance(user_id, balance)
        update_last_claim(user_id)
        await update.message.reply_text(
            'Вы получили 80 тугриков! Следующий подарок можно получить через 12 часов.',
            reply_markup=get_keyboard(user_id)
        )
    except Exception as e:
        print(f"Ошибка в функции daily: {e}")
        await update.message.reply_text(
            'Произошла ошибка при обработке команды. Попробуйте позже.',
            reply_markup=get_keyboard(user_id)
        )


# Функция для просмотра статистики (только для администраторов)
async def bot_stats(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in config.ADMIN_IDS:
        await update.message.reply_text(
            'У вас нет доступа к статистике бота.',
            reply_markup=get_keyboard(user_id)
        )
        return
    
    # Получаем статистику
    total_users = get_total_users()
    total_logins = get_total_logins()
    
    # Формируем сообщение со статистикой
    stats_message = (
        f"📊 Статистика бота:\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🔄 Общее количество входов: {total_logins}"
    )
    
    await update.message.reply_text(
        stats_message,
        reply_markup=get_keyboard(user_id)
    )


# Обработчик текстовых сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user_id = update.message.from_user.id
    
    if text == 'Играть':
        await slots_start(update, context)
    elif text == 'Баланс':
        await balance(update, context)
    elif text == 'Ежедневная награда':
        await daily(update, context)
    elif text == 'Статистика бота':
        await bot_stats(update, context)
    else:
        await update.message.reply_text(
            'Неизвестная команда.',
            reply_markup=get_keyboard(user_id)
        )


def main() -> None:
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("stats", bot_stats))  

    # Обработчик для игры в слоты
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('slots', slots_start),
                     MessageHandler(filters.Regex('^Играть$'), slots_start)],
        states={
            WAITING_FOR_BET: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bet)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex('^Играть$'),
        handle_message
    ))

    application.run_polling()
    application.idle()


if __name__ == '__main__':
    main()
