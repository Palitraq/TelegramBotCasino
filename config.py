# Конфигурационный файл для хранения чувствительных данных

# Токен Telegram бота (BotFather))
BOT_TOKEN = "7514444798:AAGavu9pJBYauDYvTCHodQXzITi2eNuuxvY"

# ID администраторов (можно добавить несколько)
ADMIN_IDS = [
    1056718337,  # Замените на ваш реальный Telegram user ID
]

# Настройки базы данных
DATABASE_PATH = 'casino_bot.db'

# Настройки игры
DAILY_REWARD_AMOUNT = 80
DAILY_REWARD_COOLDOWN = 12 * 3600  # 12 часов в секундах

# Настройки слотов
MIN_BET = 10
MAX_BET = 1000
SLOT_SYMBOLS = ['🍎', '🍌', '🍓', '🍒', '🍑']
SLOT_MULTIPLIER = 5
