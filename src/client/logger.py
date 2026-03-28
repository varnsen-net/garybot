"""
sqlite> .schema user_logs
CREATE TABLE user_logs (
            nick text,
            target text,
            message text,
            timestamp real);
"""
import sqlite3
import gevent
from gevent.queue import Queue, Empty
from loguru import logger


class Logger(gevent.Greenlet):

    def __init__(self, stop_event, app_config):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self._stop_event = stop_event
        self._user_logs_path = app_config.user_logs_path
        self._conn = None

    def _write(self, entry):
        if entry.message.startswith('.'):
            return
        try:
            self._conn.execute(
                "INSERT INTO user_logs VALUES (?, ?, ?, ?)",
                (entry.nick, entry.target, entry.message, entry.timestamp)
            )
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Logger write failed: {e}")

    def _run(self):
        self._conn = sqlite3.connect(self._user_logs_path)
        self._conn.execute('''CREATE TABLE IF NOT EXISTS user_logs
                             (nick text, target text, message text, timestamp real)''')
        self._conn.commit()
        logger.info("Logger started...")
        try:
            while not self._stop_event.is_set():
                try:
                    entry = self.inbox.get(timeout=1)
                except Empty:
                    continue
                self._write(entry)
        finally:
            if self._conn:
                self._conn.close()
