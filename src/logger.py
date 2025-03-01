import traceback
import time

import sqlite3


def log_msg(message_payload):
    """Write channel message to file."""
    row = [message_payload['nick'],
           message_payload['target'],
           message_payload['message'],
           message_payload['timestamp']]
    with sqlite3.connect("./user_logs.db") as db:
        db.execute(
            "INSERT INTO user_logs (nick, target, message, timestamp) VALUES (?, ?, ?, ?)",
            row)
        db.commit()
    return


def log_error() -> None:
    """Write error message to file."""
    error_timestamp = str(time.asctime())
    with open("./error-log.txt", "a+", encoding="utf-8") as error_log:
        error_log.write(error_timestamp + "\r\n")
        traceback.print_exc(file=error_log)
        error_log.write("\r\n")
    return
