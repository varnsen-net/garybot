"""
sqlite> .schema user_logs
CREATE TABLE user_logs (
            nick text,
            target text,
            message text,
            timestamp real);
"""
import sqlite3


def irc_logger(nick, target, message, timestamp, user_logs_path):
    """Create table if it doesn't exist, then insert log into database."""
    if not message.startswith('.'):
        conn = sqlite3.connect(user_logs_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_logs
                     (nick text, target text, message text, timestamp real)''')
        c.execute("INSERT INTO user_logs VALUES (?, ?, ?, ?)",
                  (nick, target, message, timestamp))
        conn.commit()
        conn.close()
