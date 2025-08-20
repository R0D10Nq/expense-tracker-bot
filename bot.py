# Главный файл бота

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from handlers import (
	start, help_command, add_expense, show_stats,
	show_month_stats, show_category_stats, delete_last,
	export_data, set_budget, check_budget
)
from database import init_db

# Настройка логирования
logging.basicConfig (
	format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level = logging.INFO
)
logger = logging.getLogger (__name__)


def main ():
	"""Запуск бота"""
	# Инициализация базы данных
	init_db ()
	
	# Создание приложения
	application = Application.builder ().token (BOT_TOKEN).build ()
	
	# Регистрация обработчиков
	application.add_handler (CommandHandler ("start", start))
	application.add_handler (CommandHandler ("help", help_command))
	application.add_handler (CommandHandler ("stats", show_stats))
	application.add_handler (CommandHandler ("month", show_month_stats))
	application.add_handler (CommandHandler ("category", show_category_stats))
	application.add_handler (CommandHandler ("delete", delete_last))
	application.add_handler (CommandHandler ("export", export_data))
	application.add_handler (CommandHandler ("budget", set_budget))
	application.add_handler (CommandHandler ("check_budget", check_budget))
	
	# Обработчик для добавления расходов
	application.add_handler (MessageHandler (filters.TEXT & ~filters.COMMAND, add_expense))
	
	# Обработчик callback кнопок
	application.add_handler (CallbackQueryHandler (show_category_stats, pattern = "^category_"))
	
	# Запуск бота
	application.run_polling (allowed_updates = True)


if __name__ == '__main__':
	main ()