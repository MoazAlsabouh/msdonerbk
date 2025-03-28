from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# دالة لإنشاء قاعدة البيانات والجداول إذا لم تكن موجودة
def init_db():
    conn = sqlite3.connect('restaurant.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            total_income REAL,
            total_expense REAL,
            record_date TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS income_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            source TEXT,
            amount REAL,
            FOREIGN KEY(record_id) REFERENCES daily_records(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER,
            item TEXT,
            amount REAL,
            FOREIGN KEY(record_id) REFERENCES daily_records(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# نقطة النهاية لحفظ البيانات وإرجاع ملف JSON يحتوي على النتيجة
@app.route('/save', methods=['POST'])
def save_data():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400

    start_time = data.get('start_time')
    end_time = data.get('end_time')
    incomes = data.get('incomes', [])
    expenses = data.get('expenses', [])
    
    total_income = sum(item.get('amount', 0) for item in incomes)
    total_expense = sum(item.get('amount', 0) for item in expenses)
    record_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('restaurant.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO daily_records (start_time, end_time, total_income, total_expense, record_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (start_time, end_time, total_income, total_expense, record_date))
    record_id = c.lastrowid
    
    for income in incomes:
        c.execute('''
            INSERT INTO income_details (record_id, source, amount)
            VALUES (?, ?, ?)
        ''', (record_id, income.get('source'), income.get('amount')))
    
    for expense in expenses:
        c.execute('''
            INSERT INTO expense_details (record_id, item, amount)
            VALUES (?, ?, ?)
        ''', (record_id, expense.get('item'), expense.get('amount')))
    
    conn.commit()
    conn.close()
    
    # إعداد الملف JSON للإرجاع مع تفاصيل العملية
    response_data = {
        'status': 'success',
        'record_id': record_id,
        'start_time': start_time,
        'end_time': end_time,
        'total_income': total_income,
        'total_expense': total_expense,
        'record_date': record_date,
        'incomes': incomes,
        'expenses': expenses
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
