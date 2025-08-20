# Вспомогательные функции

import re
from typing import Dict, Optional

# Маппинг эмодзи на категории
EMOJI_TO_CATEGORY = {
	"🍔": "Еда",
	"🍕": "Еда",
	"🍜": "Еда",
	"☕": "Еда",
	"🚗": "Транспорт",
	"🚕": "Транспорт",
	"🚇": "Транспорт",
	"🏠": "Жилье",
	"🏡": "Жилье",
	"💊": "Здоровье",
	"💉": "Здоровье",
	"🎮": "Развлечения",
	"🎬": "Развлечения",
	"🎭": "Развлечения",
	"🛒": "Покупки",
	"👕": "Покупки",
	"👟": "Покупки",
	"📚": "Образование",
	"📖": "Образование",
	"💰": "Другое"
}


def parse_expense (text: str) -> Optional [Dict]:
	"""
	Парсинг текста расхода
	Примеры:
	- "100 обед" -> {amount: 100, category: "Другое", description: "обед"}
	- "250 🍔 бургер" -> {amount: 250, category: "Еда", description: "бургер"}
	"""
	# Паттерн для парсинга
	pattern = r'^(\d+(?:\.\d+)?)\s*([^\s]*?)\s*(.*)$'
	match = re.match (pattern, text.strip ())
	
	if not match:
		return None
	
	amount = float (match.group (1))
	emoji_or_desc = match.group (2)
	rest = match.group (3)
	
	# Определяем категорию
	category = "Другое"
	description = ""
	
	# Проверяем, есть ли эмодзи
	if emoji_or_desc in EMOJI_TO_CATEGORY:
		category = EMOJI_TO_CATEGORY [emoji_or_desc]
		description = rest.strip () if rest else category.lower ()
	else:
		# Если нет эмодзи, все после суммы - описание
		description = f"{emoji_or_desc} {rest}".strip ()
		if not description:
			description = "Без описания"
	
	return {
		'amount': amount,
		'category': category,
		'description': description
	}


def format_stats (stats: Dict) -> str:
	"""Форматирование статистики для отображения"""
	text = f"""
📊 <b>Статистика за {stats ['days']} дней</b>

💰 Всего потрачено: {stats ['total']:.0f}₽
📅 Средний расход в день: {stats ['avg_daily']:.0f}₽

<b>По категориям:</b>
"""
	
	if stats ['by_category']:
		for category, total, count in stats ['by_category']:
			percentage = (total / stats ['total'] * 100) if stats ['total'] > 0 else 0
			text += f"• {category}: {total:.0f}₽ ({percentage:.0f}%, {count} шт.)\n"
	
	return text


def create_expense_chart (expenses: list) -> bytes:
	"""
	Создание графика расходов (заглушка)
	В реальном проекте здесь можно использовать matplotlib
	"""
	# TODO: Реализовать создание графиков
	pass