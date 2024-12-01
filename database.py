import sqlite3
import datetime
import config

def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Создаем таблицу users с правильными типами данных
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER NOT NULL DEFAULT 0,
        last_claim TIMESTAMP,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем таблицу для логирования входов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_logs (
        user_id INTEGER,
        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def log_user_login(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_logs (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['balance'] if result else 0

def update_user_balance(user_id, balance):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO users (user_id, balance) VALUES (?, ?)
    ON CONFLICT(user_id) DO UPDATE SET balance = ?
    ''', (user_id, balance, balance))
    conn.commit()
    conn.close()

def get_last_claim(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT last_claim FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['last_claim'] if result and result['last_claim'] else None

def update_last_claim(user_id):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute('''
    INSERT INTO users (user_id, last_claim, balance) 
    VALUES (?, ?, COALESCE((SELECT balance FROM users WHERE user_id = ?), 0))
    ON CONFLICT(user_id) DO UPDATE SET last_claim = ?
    ''', (user_id, now, user_id, now))
    conn.commit()
    conn.close()

def get_total_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(DISTINCT user_id) as total_users FROM users')
    result = cursor.fetchone()
    conn.close()
    return result['total_users']

def get_total_logins():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total_logins FROM user_logs')
    result = cursor.fetchone()
    conn.close()
    return result['total_logins']

def is_admin(user_id):
    return user_id in config.ADMIN_IDS

def set_admin(user_id):
    """
    Добавляет пользователя в список администраторов в config.py
    
    :param user_id: Telegram User ID администратора
    """
    if user_id not in config.ADMIN_IDS:
        # Открываем файл и читаем его содержимое
        with open('config.py', 'r') as f:
            content = f.readlines()
        
        # Находим строку с ADMIN_IDS
        for i, line in enumerate(content):
            if line.strip().startswith('ADMIN_IDS'):
                # Добавляем нового администратора
                content[i] = line.rstrip() + f', {user_id}  # Добавлен автоматически\n'
                break
        
        # Записываем изменения обратно в файл
        with open('config.py', 'w') as f:
            f.writelines(content)
        
        # Обновляем список в текущей сессии
        config.ADMIN_IDS.append(user_id)
        print(f'Пользователь {user_id} добавлен в список администраторов.')
    else:
        print(f'Пользователь {user_id} уже является администратором.')

# Инициализируем базу данных при импорте модуля
init_db()
