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
    """A simple logger that writes user messages to a SQLite database.

    The Logger runs in a separate greenlet and listens for log entries on its
    inbox queue.

    Attributes:
        inbox (Queue): A queue for receiving log entries.
        _stop_event (Event): An event to signal the logger to stop.
        _user_logs_path (str): The file path to the SQLite database for user
            logs.
        _conn (sqlite3.Connection): The SQLite connection object.
    """

    def __init__(self, stop_event, app_config):
        gevent.Greenlet.__init__(self)
        self.inbox = Queue()
        self._stop_event = stop_event
        self._user_logs_path = app_config.user_logs_path
        self._conn = None

    def _write(self, entry):
        """Writes a log entry to the SQLite database.

        :param ParsedMessage entry: The log entry to write, containing the
            nick, target, message, and timestamp.
        :return: None
        :rtype: None
        """
        try:
            self._conn.execute(
                "INSERT INTO user_logs VALUES (?, ?, ?, ?)",
                (entry.nick, entry.target, entry.message, entry.timestamp)
            )
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Logger write failed: {e}")

    def _run(self):
        """The main loop of the Logger greenlet. It initializes the SQLite
        connection and listens for log entries until the stop event is set.

        :return: None
        :rtype: None
        """
        self._conn = sqlite3.connect(self._user_logs_path)
        self._conn.execute('''CREATE TABLE IF NOT EXISTS user_logs
                             (nick text, target text, message text, timestamp real)''')
        self._conn.commit()
        logger.info("Logger started.")
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
