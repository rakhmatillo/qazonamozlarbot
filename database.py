import sqlite3
from datetime import datetime

def init_db():
    """Initialize the database with prayers and history tables"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    # Main prayers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missed_prayers (
            user_id INTEGER PRIMARY KEY,
            bomdod INTEGER DEFAULT 0,
            peshin INTEGER DEFAULT 0,
            asr INTEGER DEFAULT 0,
            shom INTEGER DEFAULT 0,
            xufton INTEGER DEFAULT 0,
            vitr INTEGER DEFAULT 0,
            setup_completed INTEGER DEFAULT 0
        )
    ''')
    
    # History table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prayer_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prayer_name TEXT,
            action TEXT,
            amount INTEGER,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES missed_prayers(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def is_setup_completed(user_id):
    """Check if user has completed initial setup"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT setup_completed FROM missed_prayers WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result and result[0] == 1

def get_user_prayers(user_id):
    """Get missed prayers for a user"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM missed_prayers WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result is None:
        # Create new user entry
        cursor.execute('''
            INSERT INTO missed_prayers (user_id, setup_completed) VALUES (?, 0)
        ''', (user_id,))
        conn.commit()
        result = (user_id, 0, 0, 0, 0, 0, 0, 0)
    
    conn.close()
    return {
        'bomdod': result[1],
        'peshin': result[2],
        'asr': result[3],
        'shom': result[4],
        'xufton': result[5],
        'vitr': result[6]
    }

def save_initial_prayers(user_id, prayers):
    """Save initial prayer counts and mark setup as complete"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    # First, ensure user exists
    cursor.execute('SELECT user_id FROM missed_prayers WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO missed_prayers (user_id, bomdod, peshin, asr, shom, xufton, vitr, setup_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (user_id, prayers['bomdod'], prayers['peshin'], prayers['asr'], 
              prayers['shom'], prayers['xufton'], prayers['vitr']))
    else:
        cursor.execute('''
            UPDATE missed_prayers 
            SET bomdod = ?, peshin = ?, asr = ?, shom = ?, xufton = ?, vitr = ?, setup_completed = 1
            WHERE user_id = ?
        ''', (prayers['bomdod'], prayers['peshin'], prayers['asr'], 
              prayers['shom'], prayers['xufton'], prayers['vitr'], user_id))
    
    conn.commit()
    conn.close()
    
    # Add to history
    for prayer_name, count in prayers.items():
        if count > 0:
            add_history(user_id, prayer_name, 'initial_setup', count)

def update_prayer(user_id, prayer_name, amount, action='add'):
    """Add or subtract missed prayers"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    # Ensure user exists
    get_user_prayers(user_id)
    
    cursor.execute(f'''
        UPDATE missed_prayers 
        SET {prayer_name} = MAX(0, {prayer_name} + ?)
        WHERE user_id = ?
    ''', (amount, user_id))
    
    conn.commit()
    conn.close()
    
    # Add to history
    add_history(user_id, prayer_name, action, abs(amount))

def get_total_missed(user_id):
    """Get total number of missed prayers"""
    prayers = get_user_prayers(user_id)
    return sum(prayers.values())

def add_history(user_id, prayer_name, action, amount):
    """Add entry to history"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO prayer_history (user_id, prayer_name, action, amount, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, prayer_name, action, amount, timestamp))
    
    conn.commit()
    conn.close()

def get_history(user_id, limit=10):
    """Get recent history for a user"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT prayer_name, action, amount, timestamp
        FROM prayer_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def reset_user_setup(user_id):
    """Reset user setup to allow re-entering initial values"""
    conn = sqlite3.connect('prayers.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE missed_prayers 
        SET setup_completed = 0
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()