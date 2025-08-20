from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re
from datetime import datetime
import csv
import io
from database import (
	add_expense as db_add_expense,
	get_user_stats,
	get_month_stats,
	delete_last_expense,
	get_all_expenses,
	set_monthly_budget,
	get_budget_info
)
from utils import parse_expense, format_stats, create_expense_chart

# Категории расходов
CATEGORIES = {
	"🍔": "Еда",
	"🚗": "Транспорт",
	"🏠": "Жилье",
	"💊": "Здоровье",
	"🎮": "Развлечения",
	"🛒": "Покупки",
	"📚": "Образование",
	"💰": "Другое"
}


async def start (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик команды /start"""
	user = update.effective_user
	welcome_text = f"""
👋 Привет, {user.first_name}!

Я помогу тебе контролировать расходы.

📝 Чтобы добавить расход, просто отправь сообщение в формате:
<code>100 кофе</code> или <code>100 🍔 бургер</code>

📊 Доступные команды:
/help - Подробная справка
/stats - Статистика за 30 дней
/month - Статистика за текущий месяц
/category - Статистика по категориям
/budget - Установить месячный бюджет
/check_budget - Проверить бюджет
/delete - Удалить последний расход
/export - Экспорт данных в CSV

Начни прямо сейчас! Отправь свой первый расход.
    """
	await update.message.reply_text (welcome_text, parse_mode = 'HTML')


async def help_command (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Обработчик команды /help"""
	help_text = """
📚 <b>Подробная справка</b>

<b>Добавление расходов:</b>
• <code>100 обед</code> - добавит 100₽ в категорию "Другое"
• <code>250 🍔 бургер</code> - добавит 250₽ в категорию "Еда"
• <code>1500 🚗</code> - добавит 1500₽ в категорию "Транспорт"

<b>Доступные категории:</b>
🍔 - Еда
🚗 - Транспорт
🏠 - Жилье
💊 - Здоровье
🎮 - Развлечения
🛒 - Покупки
📚 - Образование
💰 - Другое

<b>Команды:</b>
/stats - Общая статистика за 30 дней
/month - Детальная статистика за месяц
/category - Статистика по категориям
/budget <code>сумма</code> - Установить месячный бюджет
/check_budget - Проверить остаток бюджета
/delete - Удалить последнюю запись
/export - Скачать все данные в CSV

<b>Примеры:</b>
• <code>50 кофе</code>
• <code>2000 🏠 квартплата</code>
• <code>300 🍔 доставка еды</code>
• <code>/budget 50000</code>
    """
	await update.message.reply_text (help_text, parse_mode = 'HTML')


async def add_expense (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Добавление нового расхода"""
	user_id = update.effective_user.id
	text = update.message.text
	
	# Парсинг сообщения
	expense_data = parse_expense (text)
	
	if not expense_data:
		await update.message.reply_text (
			"❌ Не понял формат. Используй:\n"
			"<code>100 обед</code> или <code>100 🍔 бургер</code>",
			parse_mode = 'HTML'
		)
		return
	
	# Добавление в БД
	expense_id = db_add_expense (
		user_id = user_id,
		amount = expense_data ['amount'],
		category = expense_data ['category'],
		description = expense_data ['description']
	)
	
	# Проверка бюджета
	budget_info = get_budget_info (user_id)
	budget_warning = ""
	
	if budget_info:
		remaining = budget_info ['remaining']
		percentage = budget_info ['percentage']
		
		if remaining < 0:
			budget_warning = f"\n\n⚠️ <b>Превышен бюджет на {abs (remaining):.0f}₽!</b>"
		elif percentage > 80:
			budget_warning = f"\n\n⚠️ Использовано {percentage:.0f}% месячного бюджета"
	
	response_text = (
		f"✅ Добавлено: {expense_data ['amount']}₽\n"
		f"📁 Категория: {expense_data ['category']}\n"
		f"📝 Описание: {expense_data ['description'] or 'Без описания'}"
		f"{budget_warning}"
	)
	
	await update.message.reply_text (response_text, parse_mode = 'HTML')


async def show_stats (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Показать статистику за 30 дней"""
	user_id = update.effective_user.id
	stats = get_user_stats (user_id, days = 30)
	
	if stats ['total'] == 0:
		await update.message.reply_text ("📊 У вас пока нет расходов за последние 30 дней")
		return
	
	stats_text = format_stats (stats)
	await update.message.reply_text (stats_text, parse_mode = 'HTML')


async def show_month_stats (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Статистика за текущий месяц"""
	user_id = update.effective_user.id
	stats = get_month_stats (user_id)
	
	if stats ['total'] == 0:
		await update.message.reply_text (f"📊 У вас пока нет расходов за {stats ['month']}")
		return
	
	text = f"""
📊 <b>Статистика за {stats ['month']}</b>

💰 Всего потрачено: {stats ['total']:.0f}₽
📝 Количество трат: {stats ['count']}
📅 Средний расход в день: {stats ['total'] / len (stats ['daily_expenses']):.0f}₽

<b>По дням:</b>
"""
	
	for date_str, amount in stats ['daily_expenses'] [-10:]:
		date_obj = datetime.strptime (date_str, '%Y-%m-%d')
		text += f"• {date_obj.strftime ('%d.%m')}: {amount:.0f}₽\n"
	
	if len (stats ['daily_expenses']) > 10:
		text += f"\n<i>...и ещё {len (stats ['daily_expenses']) - 10} дней</i>"
	
	await update.message.reply_text (text, parse_mode = 'HTML')


async def show_category_stats (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Статистика по категориям"""
	user_id = update.effective_user.id
	
	# Если это callback от кнопки
	if update.callback_query:
		await update.callback_query.answer ()
		category = update.callback_query.data.replace ("category_", "")
		# Здесь можно показать детальную статистику по категории
		await update.callback_query.message.reply_text (
			f"Детальная статистика по категории {category} в разработке..."
		)
		return
	
	stats = get_user_stats (user_id, days = 30)
	
	if not stats ['by_category']:
		await update.message.reply_text ("📊 У вас пока нет расходов")
		return
	
	# Создаем кнопки для категорий
	keyboard = []
	for category, total, count in stats ['by_category']:
		button_text = f"{category}: {total:.0f}₽ ({count})"
		keyboard.append ([InlineKeyboardButton (button_text, callback_data = f"category_{category}")])
	
	reply_markup = InlineKeyboardMarkup (keyboard)
	
	text = "📊 <b>Расходы по категориям за 30 дней:</b>\n\nНажмите на категорию для подробностей:"
	
	await update.message.reply_text (text, reply_markup = reply_markup, parse_mode = 'HTML')


async def delete_last (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Удалить последний расход"""
	user_id = update.effective_user.id
	
	if delete_last_expense (user_id):
		await update.message.reply_text ("✅ Последний расход удален")
	else:
		await update.message.reply_text ("❌ Нет расходов для удаления")


async def export_data (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Экспорт данных в CSV"""
	user_id = update.effective_user.id
	expenses = get_all_expenses (user_id)
	
	if not expenses:
		await update.message.reply_text ("📊 У вас пока нет данных для экспорта")
		return
	
	# Создание CSV файла
	output = io.StringIO ()
	writer = csv.writer (output)
	writer.writerow (['Дата', 'Сумма', 'Категория', 'Описание'])
	
	for expense in expenses:
		date = datetime.strptime (expense [0], '%Y-%m-%d %H:%M:%S')
		writer.writerow ([
			date.strftime ('%d.%m.%Y %H:%M'),
			expense [1],
			expense [2],
			expense [3] or ''
		])
	
	# Отправка файла
	output.seek (0)
	await update.message.reply_document (
		document = io.BytesIO (output.getvalue ().encode ('utf-8')),
		filename = f'expenses_{datetime.now ().strftime ("%Y%m%d")}.csv',
		caption = "📊 Ваши расходы в формате CSV"
	)


async def set_budget (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Установка месячного бюджета"""
	user_id = update.effective_user.id
	
	if not context.args:
		await update.message.reply_text (
			"❌ Укажите сумму бюджета\n"
			"Пример: <code>/budget 50000</code>",
			parse_mode = 'HTML'
		)
		return
	
	try:
		budget = float (context.args [0])
		if budget <= 0:
			raise ValueError ()
		
		set_monthly_budget (user_id, budget)
		
		await update.message.reply_text (
			f"✅ Месячный бюджет установлен: {budget:.0f}₽\n"
			f"Используйте /check_budget для проверки"
		)
	except ValueError:
		await update.message.reply_text ("❌ Некорректная сумма")


async def check_budget (update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Проверка бюджета"""
	user_id = update.effective_user.id
	budget_info = get_budget_info (user_id)
	
	if not budget_info:
		await update.message.reply_text (
			"❌ Бюджет не установлен\n"
			"Используйте /budget для установки"
		)
		return
	
	emoji = "✅" if budget_info ['remaining'] >= 0 else "❌"
	
	text = f"""
💰 <b>Бюджет на месяц: {budget_info ['budget']:.0f}₽</b>

📊 Потрачено: {budget_info ['spent']:.0f}₽ ({budget_info ['percentage']:.0f}%)
{emoji} Осталось: {budget_info ['remaining']:.0f}₽

{"⚠️ <b>Бюджет превышен!</b>" if budget_info ['remaining'] < 0 else ""}
    """
	
	await update.message.reply_text (text, parse_mode = 'HTML')
