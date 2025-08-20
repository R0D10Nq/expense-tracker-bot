# Конфиг

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("Не указан BOT_TOKEN в файле .env")

# Другие настройки
DEFAULT_CURRENCY = "₽"
MAX_DESCRIPTION_LENGTH = 100