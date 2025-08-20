# Работа с БД

import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

DB_NAME = 'expenses.db'


def init_db ():
	"""Инициализация базы данных"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	# Таблица расходов
	cursor.execute ('''
                    CREATE TABLE IF NOT EXISTS expenses
                    (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id     INTEGER NOT NULL,
                        amount      REAL    NOT NULL,
                        category    TEXT    NOT NULL,
                        description TEXT,
                        date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
	               ''')
	
	# Таблица бюджетов
	cursor.execute ('''
                    CREATE TABLE IF NOT EXISTS budgets
                    (
                        user_id        INTEGER PRIMARY KEY,
                        monthly_budget REAL NOT NULL,
                        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
	               ''')
	
	conn.commit ()
	conn.close ()


def add_expense (user_id: int, amount: float, category: str, description: str = None) -> int:
	"""Добавление нового расхода"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	cursor.execute ('''
                    INSERT INTO expenses (user_id, amount, category, description)
                    VALUES (?, ?, ?, ?)
	               ''', (user_id, amount, category, description))
	
	expense_id = cursor.lastrowid
	conn.commit ()
	conn.close ()
	
	return expense_id


def get_user_stats (user_id: int, days: int = 30) -> Dict:
	"""Получение статистики пользователя"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	date_from = datetime.now () - timedelta (days = days)
	
	# Общая сумма
	cursor.execute ('''
                    SELECT SUM(amount)
                    FROM expenses
                    WHERE user_id = ?
                      AND date >= ?
	               ''', (user_id, date_from))
	total = cursor.fetchone () [0] or 0
	
	# По категориям
	cursor.execute ('''
                    SELECT category, SUM(amount), COUNT(*)
                    FROM expenses
                    WHERE user_id = ?
                      AND date >= ?
                    GROUP BY category
                    ORDER BY SUM(amount) DESC
	               ''', (user_id, date_from))
	by_category = cursor.fetchall ()
	
	# Средний расход в день
	cursor.execute ('''
                    SELECT AVG(daily_total)
                    FROM (SELECT DATE(date) as day, SUM(amount) as daily_total
                          FROM expenses
                          WHERE user_id = ?
                            AND date >= ?
                          GROUP BY DATE(date))
	               ''', (user_id, date_from))
	avg_daily = cursor.fetchone () [0] or 0
	
	conn.close ()
	
	return {
		'total': total,
		'by_category': by_category,
		'avg_daily': avg_daily,
		'days': days
	}


def get_month_stats (user_id: int) -> Dict:
	"""Статистика за текущий месяц"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	# Начало текущего месяца
	now = datetime.now ()
	month_start = datetime (now.year, now.month, 1)
	
	cursor.execute ('''
                    SELECT SUM(amount), COUNT(*)
                    FROM expenses
                    WHERE user_id = ?
                      AND date >= ?
	               ''', (user_id, month_start))
	
	result = cursor.fetchone ()
	total = result [0] or 0
	count = result [1] or 0
	
	# По дням
	cursor.execute ('''
                    SELECT DATE(date), SUM(amount)
                    FROM expenses
                    WHERE user_id = ?
                      AND date >= ?
                    GROUP BY DATE(date)
                    ORDER BY DATE(date)
	               ''', (user_id, month_start))
	daily_expenses = cursor.fetchall ()
	
	conn.close ()
	
	return {
		'total': total,
		'count': count,
		'daily_expenses': daily_expenses,
		'month': now.strftime ('%B %Y')
	}


def delete_last_expense (user_id: int) -> bool:
	"""Удаление последнего расхода"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	cursor.execute ('''
                    DELETE
                    FROM expenses
                    WHERE id = (SELECT id
                                FROM expenses
                                WHERE user_id = ?
                                ORDER BY date DESC
                                LIMIT 1)
	               ''', (user_id,))
	
	deleted = cursor.rowcount > 0
	conn.commit ()
	conn.close ()
	
	return deleted


def get_all_expenses (user_id: int) -> List [Tuple]:
	"""Получение всех расходов пользователя"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	cursor.execute ('''
                    SELECT date, amount, category, description
                    FROM expenses
                    WHERE user_id = ?
                    ORDER BY date DESC
	               ''', (user_id,))
	
	expenses = cursor.fetchall ()
	conn.close ()
	
	return expenses


def set_monthly_budget (user_id: int, budget: float):
	"""Установка месячного бюджета"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	cursor.execute ('''
        INSERT OR REPLACE INTO budgets (user_id, monthly_budget)
        VALUES (?, ?)
    ''', (user_id, budget))
	
	conn.commit ()
	conn.close ()


def get_budget_info (user_id: int) -> Dict:
	"""Получение информации о бюджете"""
	conn = sqlite3.connect (DB_NAME)
	cursor = conn.cursor ()
	
	# Получаем бюджет
	cursor.execute ('SELECT monthly_budget FROM budgets WHERE user_id = ?', (user_id,))
	result = cursor.fetchone ()
	
	if not result:
		conn.close ()
		return None
	
	budget = result [0]
	
	# Получаем расходы за текущий месяц
	now = datetime.now ()
	month_start = datetime (now.year, now.month, 1)
	
	cursor.execute ('''
                    SELECT SUM(amount)
                    FROM expenses
                    WHERE user_id = ?
                      AND date >= ?
	               ''', (user_id, month_start))
	
	spent = cursor.fetchone () [0] or 0
	conn.close ()
	
	return {
		'budget': budget,
		'spent': spent,
		'remaining': budget - spent,
		'percentage': (spent / budget * 100) if budget > 0 else 0
	}